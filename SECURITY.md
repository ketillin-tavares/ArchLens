# Segurança — ArchLens

> Este documento descreve os controles de segurança do ambiente de produção (AWS/EC2) do ArchLens.
> Cada controle citado possui referência ao artefato que o implementa no repositório.

---

## 1. Visão geral

O ArchLens é um sistema de microsserviços back-end que recebe diagramas de arquitetura (imagem/PDF), processa de forma assíncrona e delega a análise a um modelo de linguagem de grande porte (LLM), devolvendo um relatório técnico estruturado. Por lidar com arquivos enviados por usuários externos, acionar APIs de IA de terceiros e persistir resultados em banco de dados e object storage, o sistema é exposto às seguintes ameaças principais:

- **Abuso de upload** — envio de arquivos maliciosos, excessivamente grandes ou de tipo indevido.
- **Prompt injection** — tentativa de manipular o comportamento da LLM via conteúdo do diagrama ou metadados.
- **Exposição de dados sensíveis** — vazamento de PII presente em diagramas para APIs externas.
- **Acesso não autorizado à API** — chamadas sem autenticação válida.
- **Comprometimento de credenciais** — exposição de chaves de banco, APIs e segredos de infraestrutura.

A postura de segurança adotada combina: controles de borda (Kong API Gateway + Clerk JWT), isolamento de rede (VPC + security groups), guardrails de IA (LiteLLM + Presidio + Pydantic), gerenciamento centralizado de segredos (AWS Secrets Manager) e observabilidade contínua (New Relic).

---

## 2. Requisitos básicos de segurança adotados

### 2.1 Autenticação na borda

| Controle | Onde implementado |
|---|---|
| SPA autentica via **Clerk** (OAuth 2.0 / OIDC) | `frontend/` — integração nativa Clerk React SDK |
| **Kong JWT plugin** valida tokens Clerk em toda requisição à API | `gateways/kong/kong.yml.template` — ativado quando `KONG_JWT_SECRET` está configurado via Secrets Manager |
| Painel administrativo do LiteLLM protegido por **master key** | `gateways/litellm/litellm_config.yaml` + `infra/terraform/05-ec2-deploy/secrets.tf` (secret `litellm`) |
| Acesso SSH restrito a IP de operador `/32` | `infra/terraform/05-ec2-deploy/security-groups.tf` (`allowed_ssh_cidr`) |
| Shell remoto via **AWS SSM Session Manager** (sem chave SSH armazenada) | `infra/terraform/05-ec2-deploy/iam.tf` (política `AmazonSSMManagedInstanceCore`) |

### 2.2 Autorização entre serviços

Os três microsserviços internos (upload, processing, report) comunicam-se na rede Docker interna sem exposição direta à internet. O Kong é o único ponto de entrada externo. Não há mTLS entre serviços internos (ver Seção 9).

### 2.3 Segregação de rede

- **VPC** dedicada com subnets públicas (EC2) e privadas (RDS).
- **RDS em subnet privada**: o banco de dados não possui IP público; o security group `archlens-ec2-rds-sg` aceita conexões na porta 5432 exclusivamente a partir do security group do EC2.
- **IMDSv2 obrigatório** no EC2 (`http_tokens = "required"`), prevenindo SSRF via Instance Metadata Service.

Arquivo de referência: `infra/terraform/05-ec2-deploy/security-groups.tf`, `vpc.tf`, `rds.tf`.

### 2.4 Gerenciamento de segredos

Todos os segredos de produção são armazenados no **AWS Secrets Manager**, sob o prefixo `archlens/<environment>/`. Os containers consomem-nos via script de bootstrap que cria arquivos `.env` em `/opt/archlens/secrets/` — esses arquivos não existem na imagem Docker.

O EC2 acessa o Secrets Manager via IAM instance profile (sem chaves de acesso estáticas). Detalhado na Seção 7.

### 2.5 Políticas de IAM

A IAM role do EC2 (`archlens-ec2-profile`) adota o princípio de menor privilégio:

| Ação | Escopo |
|---|---|
| `secretsmanager:GetSecretValue`, `DescribeSecret` | Apenas secrets sob `archlens/<env>/*` |
| `secretsmanager:PutSecretValue`, `UpdateSecret` | Apenas secrets `processing` e `report` (bootstrap) |
| `s3:GetObject`, `PutObject`, `DeleteObject`, `ListBucket` | Apenas bucket `archlens-ec2-diagramas-*` |
| ECR read-only | Managed policy `AmazonEC2ContainerRegistryReadOnly` |
| SSM Session Manager | Managed policy `AmazonSSMManagedInstanceCore` |

Arquivo de referência: `infra/terraform/05-ec2-deploy/iam.tf`.

### 2.6 Criptografia em repouso

| Recurso | Status |
|---|---|
| Volume EBS raiz do EC2 | Cifrado (gp3, chave gerenciada pela AWS) |
| AWS Secrets Manager | Cifrado (KMS gerenciado pela AWS) |
| S3 — diagramas | Acesso público totalmente bloqueado (`block_public_acls`, `ignore_public_acls`, `block_public_policy`, `restrict_public_buckets`) |
| RDS — dados em repouso | **Não configurado** — ver Seção 9 |

Arquivos de referência: `infra/terraform/05-ec2-deploy/ec2.tf`, `s3.tf`, `secrets.tf`.

### 2.7 Registro de contêineres

- **Amazon ECR** com **tags imutáveis** (impede sobrescrita acidental de imagens de produção).
- **Scan on push** ativo: ECR verifica CVEs em cada imagem enviada.
- Imagens identificadas por SHA de commit (tag imutável por build).

Arquivo de referência: `infra/terraform/05-ec2-deploy/ecr.tf`.

---

## 3. Validação e tratamento de entradas não confiáveis

### 3.1 Validação de upload

A validação de arquivos enviados ocorre em três camadas independentes:

| Camada | Controle | Referência |
|---|---|---|
| Kong API Gateway | Limite de payload: **10 MB** (`request-size-limiting` plugin) | `gateways/kong/kong.yml` |
| Nginx (frontend) | `client_max_body_size 10m` | `frontend/nginx.ec2.conf` |
| Domínio (upload-service) | Tamanho máximo: 10 MB; tipos MIME permitidos: `image/png`, `image/jpeg`, `application/pdf` | `services/upload-service/src/domain/value_objects/arquivo_diagrama.py` |

O nome original do arquivo é persistido apenas como metadado de auditoria. A chave de armazenamento no S3 é gerada como UUID, prevenindo directory traversal e colisão de nomes.

### 3.2 Sanitização de payloads

Todos os schemas de entrada e saída das APIs são validados via **Pydantic** (`BaseModel` + `Field` com constraints). Payloads fora do schema resultam em HTTP 422 antes de qualquer lógica de negócio ser executada. A validação ocorre na camada Interface Adapters, sem que detalhes de parsing cheguem ao domínio.

### 3.3 Rate limiting

O Kong aplica rate limiting global de **30 requisições por minuto por IP** (`rate-limiting` plugin, política local). O controle cobre todas as rotas expostas.

Arquivo de referência: `gateways/kong/kong.yml`.

### 3.4 Segurança no frontend

O Nginx do frontend injeta os seguintes cabeçalhos HTTP de segurança em todas as respostas:

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

Uma **Content Security Policy (CSP)** restritiva é aplicada, limitando `script-src`, `connect-src`, `img-src` e demais diretivas aos domínios explicitamente necessários (Clerk, New Relic, AWS S3 para URLs pré-assinadas).

Cookies de sessão são configurados com `HttpOnly`, `Secure` e `SameSite=None`.

Arquivo de referência: `frontend/nginx.ec2.conf`.

---

## 4. Uso controlado de modelos de IA

### 4.1 Escopo dos modelos

Os modelos de LLM são acessados exclusivamente via **LiteLLM proxy** (`gateways/litellm/`). O proxy expõe apenas duas rotas virtuais internas:

- `archlens-vision` — análise de imagem do diagrama.
- `archlens-analyzer` — análise textual complementar.

Nenhum serviço acessa diretamente a API do provedor (Google Gemini). Toda requisição passa pelo proxy, que impõe as restrições abaixo.

### 4.2 Previsibilidade das respostas

- **Temperature:** `0.1` — respostas determinísticas, baixa variabilidade criativa.
- **Max tokens:** `4096` — trunca respostas excessivamente longas.
- **Timeout:** 120 segundos (rota primária), 60 segundos (fallback).
- **Formato obrigatório:** o system prompt instrui o modelo a retornar exclusivamente JSON estruturado. O pós-processamento rejeita respostas que não atendam ao schema.

### 4.3 Restrição de modelos

O proxy não expõe rotas genéricas. Apenas os modelos explicitamente listados em `litellm_config.yaml` são acessíveis. Solicitações para modelos não catalogados são rejeitadas pelo LiteLLM.

### 4.4 Controle de custos e quotas

- Modelos utilizados: Gemini Flash (tier gratuito / baixo custo).
- O LiteLLM persiste todos os requests/responses em banco de dados PostgreSQL (`store_model_in_db: true`), permitindo auditoria de consumo.
- O número máximo de retries por análise é limitado a 2 (primário + 1 tentativa de correção).

Arquivo de referência: `gateways/litellm/litellm_config.yaml`.

---

## 5. Tratamento seguro de falhas e comportamentos inesperados da IA

### 5.1 Guardrails de entrada — proteção contra prompt injection

O callback `detect_prompt_injection` do LiteLLM é aplicado **antes** de qualquer chamada ao modelo:

- **Heuristics check:** detecta padrões textuais conhecidos de injeção (ex: "ignore previous instructions").
- **Similarity check:** detecção baseada em embeddings para variações semânticas.

Requisições identificadas como injeção são bloqueadas antes de atingir o modelo.

Arquivo de referência: `gateways/litellm/litellm_config.yaml` (seção `guardrails`).

### 5.2 Guardrails de saída — validação de schema e fallback

A resposta da LLM passa por um pipeline de validação em duas etapas:

**Etapa 1 — LiteLLM (pós-chamada):**
- Valida que a resposta é JSON válido com as chaves obrigatórias (`componentes`, `riscos`).
- Remove automaticamente blocos de markdown (` ```json `) que o modelo possa inserir.
- Em caso de falha, aciona fallback para o modelo secundário (Gemini 2.5 Flash).

**Etapa 2 — processing-service (Pydantic):**
- Validação estrita de tipos, ranges e enums em cada campo.
- Validação cruzada: todas as referências de `componentes_afetados` em cada risco devem apontar para componentes existentes na lista.
- Se a validação falhar, o serviço solicita ao modelo que corrija o JSON (até 2 tentativas). Após esgotar as tentativas, a análise é marcada como `erro` e nenhum resultado parcial é persistido.

Arquivo de referência: `services/processing-service/src/domain/schemas.py`, `src/application/validation.py`.

### 5.3 LLM-as-a-Judge — avaliação de qualidade semântica

O pipeline inclui um `JudgeAgent` que atua como camada de avaliação semântica **após** as validações estruturais. O Judge recebe o resultado da análise e a imagem original do diagrama e os compara segundo quatro critérios, cada um pontuado de 0 a 10:

| Critério | O que avalia |
|---|---|
| **Completude** | Todos os componentes visualmente presentes foram identificados? |
| **Precisão** | Os componentes listados realmente existem na imagem (sem alucinação)? |
| **Classificação** | Os tipos atribuídos aos componentes estão corretos? |
| **Riscos relevantes** | Os riscos fazem sentido para a arquitetura mostrada? |

A pontuação média mínima para aprovação é **7,0/10**. Análises reprovadas lançam `AnaliseInsanaError`, que é capturada pelo pipeline e resulta em status `erro` — nenhum resultado de baixa qualidade é persistido ou devolvido ao cliente.

### 5.4 Timeouts, retries e fila de mensagens mortas

- **Timeout por chamada à LLM:** 120 segundos. Após esgotar, aciona fallback automático.
- **Cooldown do circuit breaker:** após 3 falhas consecutivas, o provider primário entra em cooldown de 30 segundos.
- **RabbitMQ DLQ:** mensagens de processamento que falham após todas as tentativas são movidas para a Dead Letter Queue. Um alerta no New Relic dispara imediatamente ao detectar ≥ 1 mensagem na DLQ, possibilitando investigação sem perda de dados.

### 5.5 Persistência segura do resultado

Resultados são persistidos apenas após validação bem-sucedida do schema Pydantic. Não há persistência de resultado parcial ou malformado. O LiteLLM persiste o log da interação (prompt + resposta) em banco separado para fins de auditoria.

---

## 6. Segurança na comunicação entre serviços

### 6.1 Comunicação interna (container-to-container)

Os microsserviços comunicam-se via:

- **HTTP REST** — upload-service → (via Kong) → clientes externos; report-service responde requisições de leitura.
- **AMQP (RabbitMQ)** — upload-service publica eventos; processing-service consome; processing-service publica resultado; report-service consome.

A comunicação ocorre dentro da rede Docker bridge `archlens`, sem exposição de portas internas ao host. A resolução DNS interna usa o nome do serviço (ex: `processing-service:8001`).

**Limitação atual:** a comunicação interna entre containers ocorre em HTTP/AMQP sem criptografia em trânsito (sem TLS/mTLS). O isolamento de rede (bridge Docker + security groups do EC2) é o controle compensatório. Ver Seção 9 para detalhes.

### 6.2 Comunicação externa

| Destino | Protocolo | Controle |
|---|---|---|
| Cliente → Kong (API) | HTTP na porta 8000 | Rate limiting, JWT auth, request size limit |
| Cliente → Nginx (SPA) | HTTP na porta 80 | Security headers, CSP |
| EC2 → Google Gemini (LLM) | HTTPS (egress via internet) | TLS 1.2+ gerenciado pelo SDK |
| EC2 → Clerk (OIDC) | HTTPS | TLS gerenciado pelo SDK |
| EC2 → New Relic | HTTPS | TLS gerenciado pelo agente NR |
| EC2 → AWS APIs (S3, Secrets Manager, ECR, SSM) | HTTPS | TLS + IAM role (sem chaves estáticas) |
| EC2 → RDS | TCP 5432 (sem TLS) | Rede privada + security group restrito |

---

## 7. Gerenciamento de segredos

### 7.1 AWS Secrets Manager como fonte de verdade

Nenhum segredo de produção existe em imagens Docker, variáveis de ambiente de build ou arquivos do repositório. Os 9 segredos abaixo são criados pelo Terraform e populados manualmente antes do primeiro deploy:

| Secret | Conteúdo |
|---|---|
| `archlens/<env>/database` | Senha master RDS + senhas de cada service user |
| `archlens/<env>/rabbitmq` | Credenciais RabbitMQ |
| `archlens/<env>/aws` | Nome do bucket S3 + região |
| `archlens/<env>/clerk` | OIDC issuer, JWT template, publishable key |
| `archlens/<env>/newrelic` | License key, account ID, user API key |
| `archlens/<env>/litellm` | Master key + chave de API Gemini |
| `archlens/<env>/processing` | Chave de API LLM (reservado para expansão) |
| `archlens/<env>/report` | Chave de API LLM (reservado para expansão) |
| `archlens/<env>/kong` | JWT secret para o plugin de autenticação do Kong |

Arquivo de referência: `infra/terraform/05-ec2-deploy/secrets.tf`.

### 7.2 Como os containers consomem os segredos

O script de bootstrap executado no provisionamento do EC2 lê os segredos via AWS CLI (autenticado pela IAM role da instância) e cria arquivos `.env` em `/opt/archlens/secrets/`. Os containers são iniciados com `env_file` apontando para esses arquivos. Os arquivos `.env` não existem na imagem Docker e não são versionados.

### 7.3 Rotação

A rotação de segredos é **manual** — não há política de rotação automática configurada no AWS Secrets Manager. Cada troca de credencial requer atualização do valor no Secrets Manager e reinicialização dos containers afetados.

---

## 8. Observabilidade e auditoria

### 8.1 Logs estruturados

Todos os microsserviços utilizam **Loguru** para emissão de logs estruturados com níveis `DEBUG`, `INFO`, `WARNING` e `ERROR`. Os logs são coletados pelo agente **New Relic APM** (Python agent via `newrelic-admin run-program`) e enviados ao New Relic Logs com retenção de 30 dias.

### 8.2 Stack de observabilidade

- **New Relic APM:** distributed tracing habilitado entre upload-service, processing-service e report-service. Todas as transações HTTP e chamadas ao broker são rastreadas.
- **Métricas customizadas de segurança/qualidade registradas:**
  - `Custom/Analise/Status/{recebido,em_processamento,analisado,erro}` — rastreabilidade de cada análise.
  - `Custom/AI/ValidationRetries` — número de retentativas de correção do JSON da LLM (eleva alerta se > 10).
  - `Custom/Analise/Falhas` — falhas no pipeline de análise.
  - `Custom/Upload/TamanhoBytes` — tamanho dos arquivos recebidos.
- **Eventos de auditoria persistidos no New Relic:**
  - `AnaliseIniciada` — registra início de cada pipeline de análise (timestamp, ID, tamanho do arquivo).
  - `AnaliseSucesso` — registra conclusão bem-sucedida.
  - `AnaliseFalha` — registra falha com causa.
- **LiteLLM request log:** todas as interações com a LLM (prompt + resposta) são persistidas no banco PostgreSQL `litellm_db` para auditoria de uso do modelo.
- **RDS CloudWatch Logs:** logs `postgresql` e `upgrade` exportados para CloudWatch.

Arquivo de referência: `docs/newrelic/alerts.md`, `docs/newrelic/README.md`.

### 8.3 Alertas com relevância de segurança

| Alerta | Condição | Severidade |
|---|---|---|
| DLQ com mensagens | ≥ 1 mensagem na Dead Letter Queue | Crítico |
| Taxa de erros elevada | > 2% (warning) / > 5% (crítico) por serviço | Warning / Crítico |
| Volume de logs de erro | > 10 erros em 5 minutos | Warning |
| Retentativas de validação de IA | > 10 retentativas | Warning |
| Confiança média da IA | < 0,75 | Warning |
| Latência do banco de dados | > 500 ms | Warning |

### 8.4 Trilhas de auditoria

Cada análise recebe um ID único (UUID) rastreável do upload até a geração do relatório, via logs estruturados e eventos New Relic. O nome original do arquivo enviado é preservado como metadado.

---

## 9. Principais riscos e limitações de segurança identificados

### 9.1 Ausência de TLS em trânsito no EC2

A instância EC2 de produção expõe as portas 80 (HTTP/SPA) e 8000 (HTTP/Kong API) sem terminação TLS. O cabeçalho `Strict-Transport-Security` está configurado no Nginx, mas não tem efeito sem HTTPS ativo. Toda comunicação entre cliente e servidor ocorre em texto claro.

**Impacto:** tokens JWT, payloads de upload e respostas da API trafegam sem criptografia na camada de transporte.

**Roadmap:** configuração planejada de certificado TLS (Let's Encrypt ou AWS ACM via ALB) em release futura.

### 9.2 Ausência de mTLS entre serviços internos

A comunicação HTTP e AMQP entre containers (upload → RabbitMQ → processing → report) ocorre sem autenticação mútua. O controle compensatório é o isolamento via rede Docker bridge, inacessível externamente.

### 9.3 RDS sem criptografia em repouso

O parâmetro `storage_encrypted` não está habilitado no módulo Terraform do RDS. Os dados do banco de dados PostgreSQL não estão cifrados em repouso no nível do EBS.

**Roadmap:** habilitar `storage_encrypted = true` no Terraform (requer snapshot + recriação da instância).

### 9.4 Possível vazamento de informação sensível em diagramas

Diagramas enviados podem conter informações sensíveis (endereços IP internos, nomes de serviços, topologias de rede, credenciais em anotações). O PII masking via Presidio cobre categorias comuns (e-mail, telefone, IP, cartão de crédito, nome de pessoa), mas não cobre informações proprietárias ou dados de negócio presentes no diagrama.

### 9.5 Ausência de WAF e proteção DDoS dedicada

Não há AWS WAF, AWS Shield ou proteção DDoS dedicada configurada. O único controle de volume é o rate limiting do Kong (30 req/min por IP). Um atacante com múltiplos IPs poderia saturar o serviço.

---

## 10. Processo de reporte de vulnerabilidades

Para reportar uma vulnerabilidade de segurança no ArchLens:

1. **Não abra uma issue pública** no repositório.
2. Utilize o recurso de **GitHub Security Advisories** do repositório para criar um reporte privado:
   `Repositório → Security → Advisories → New draft security advisory`
3. Descreva a vulnerabilidade com o máximo de detalhes possível: impacto, passos para reprodução, versão afetada e, se disponível, sugestão de mitigação.
4. O time irá responder e coordenar a divulgação responsável antes de qualquer publicação.
