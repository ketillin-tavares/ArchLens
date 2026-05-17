# Deploy ArchLens em EC2 (Docker Compose)

Deploy de toda a plataforma ArchLens em uma única instância EC2 orquestrada por `docker compose`, usando AWS gerenciado para RDS, S3 e Secrets Manager. Acesso público via DNS da própria EC2 (HTTP-only, Clerk em modo DEV).

## Visão geral

```
Internet  ──► EC2 t3.large Spot (Elastic IP, public DNS fixo)
                ├─ frontend (nginx :80)  ──► /api/* proxy ──► kong
                ├─ kong (:8000)          ──► upload / processing / report
                ├─ services (FastAPI)    ──► RDS, RabbitMQ, LiteLLM, S3
                ├─ litellm (:4000 restrito ao operator IP) ──► Gemini API
                ├─ rabbitmq, presidio-analyzer, presidio-anonymizer
                └─ newrelic-infra

AWS gerenciado:
   RDS Postgres (privado)  ·  S3 bucket (presigned URLs + CORS)  ·  Secrets Manager  ·  ECR
   SSM Session Manager (acesso shell + deploys via Run Command)
```

## Pré-requisitos

- Conta AWS com permissão de admin
- Terraform Cloud com organização `archlens`
- GitHub repo com Actions habilitadas
- AWS CLI v2 instalado localmente (para popular secrets)
- Conta New Relic com license key e account ID

---

## Etapa 1 — Provisionar infra com Terraform

### 1.1 Criar workspace no Terraform Cloud

No app.terraform.io → organization `archlens` → New Workspace → **API-driven workflow** → name **`archlens-ec2-deploy`**. (API-driven é o modo correto para Actions disparar o run.)

### 1.2 Configurar variáveis do workspace

Adicionar como **Terraform variables** (não env vars):

| Variável | Tipo | Sensível | Exemplo |
|---|---|---|---|
| `db_master_password` | string | ✅ | `<senha forte>` |
| `ec2_key_name` | string | ❌ | `archlens-ec2-key` |
| `allowed_ssh_cidr` | string | ❌ | `<seu-ip>/32` |
| `newrelic_account_id` | string | ✅ | `1234567` |
| `bootstrap_services` | bool | ❌ | `false` (deixe assim no 1º apply; troca para `true` apos popular secrets) |

Outras variáveis usam defaults (`aws_region=us-east-2`, `ec2_instance_type=t3.large`, `ec2_use_spot=true`, etc.). Ajustar via UI se quiser.

### 1.3 Criar key pair no console EC2

AWS Console → EC2 → Network & Security → Key Pairs → Create key pair:

- **Name**: `archlens-ec2-key` (mesmo valor de `ec2_key_name`)
- **Key pair type**: **ED25519** (recomendado — chave menor e mais moderna). RSA também funciona.
- **Private key file format**: **`.pem`** (formato OpenSSH)
- Não use `.ppk` (formato PuTTY)

Baixar o `.pem` e guardar. **Não é usada pelo workflow do GitHub Actions** (deploy roda via AWS SSM, sem SSH), mas serve para acesso manual de debug pelo seu terminal: `ssh -i archlens-ec2-key.pem ubuntu@<dns>`.

### 1.4 Primeiro apply via GitHub Actions (sem EC2)

Com `bootstrap_services = false` (default), este apply cria **somente** VPC, RDS, S3, ECR e Secrets Manager com placeholders. A EC2 será criada no segundo apply, depois dos secrets preenchidos.

GitHub → Actions → **"Infra: Terraform Deploy"** → Run workflow:

- **action**: `plan` (revisar) → conferir o output no summary
- Voltar e rodar de novo com **action**: `apply`
- **workspace**: `05-ec2-deploy`

> ⚠️ Sempre `plan` primeiro. O `apply` baixa o tfplan gerado pelo job anterior.

Após o apply, no summary do workflow aparecem os outputs (exceto sensíveis):
- `s3_bucket` → nome do bucket gerado
- `frontend_ecr_url`, `ecr_registry`
- Outputs `ec2_*` e `frontend_url` ficam `null` neste momento

Para ver `rds_address` (sensitive), acesse o workspace no Terraform Cloud → States → último run → outputs.

---

## Etapa 2 — Popular Secrets Manager

Os 9 secrets criados pelo Terraform têm valores **placeholder**. Preencher com valores reais via CLI ou console. Exemplo via CLI:

```bash
ENV=dev   # ou prod
REGION=us-east-2

# Database — use a mesma db_master_password do workspace e gere senhas
# fortes para os 4 users de servico.
aws secretsmanager put-secret-value --region $REGION \
  --secret-id "archlens/$ENV/database" \
  --secret-string '{
    "host":"<rds_address output>",
    "port":"5432",
    "master_user":"archlens",
    "master_password":"<db_master_password>",
    "upload_user":"upload_user",
    "upload_password":"<senha-forte>",
    "processing_user":"processing_user",
    "processing_password":"<senha-forte>",
    "report_user":"report_user",
    "report_password":"<senha-forte>",
    "litellm_user":"litellm_user",
    "litellm_password":"<senha-forte>"
  }'

aws secretsmanager put-secret-value --region $REGION \
  --secret-id "archlens/$ENV/rabbitmq" \
  --secret-string '{"user":"archlens","password":"<senha-forte>"}'

aws secretsmanager put-secret-value --region $REGION \
  --secret-id "archlens/$ENV/aws" \
  --secret-string '{"s3_bucket_name":"<s3_bucket output>","region":"us-east-2"}'

aws secretsmanager put-secret-value --region $REGION \
  --secret-id "archlens/$ENV/clerk" \
  --secret-string '{
    "CLERK_ISSUER_URL":"https://<seu-tenant>.clerk.accounts.dev",
    "CLERK_JWT_TEMPLATE":"archlens",
    "VITE_CLERK_PUBLISHABLE_KEY":"pk_test_xxx"
  }'

aws secretsmanager put-secret-value --region $REGION \
  --secret-id "archlens/$ENV/newrelic" \
  --secret-string '{
    "license_key":"<nr-license>",
    "account_id":"<nr-account>",
    "user_key":"<nr-user-key>"
  }'

aws secretsmanager put-secret-value --region $REGION \
  --secret-id "archlens/$ENV/litellm" \
  --secret-string '{
    "MASTER_KEY":"sk-<32-chars-random>",
    "gemini_api_key":"<google-ai-studio-key>"
  }'

aws secretsmanager put-secret-value --region $REGION \
  --secret-id "archlens/$ENV/kong" \
  --secret-string '{"KONG_JWT_SECRET":"<random-32-chars>"}'

# processing e report nao precisam ser preenchidos — sao populados
# automaticamente pelo bootstrap-litellm-vk.sh na 1a boot da EC2.
```

> Os secrets `processing` e `report` ficam com `LLM_API_KEY=PLACEHOLDER` até a 1ª boot da EC2 — o `bootstrap-litellm-vk.sh` gera as Virtual Keys e atualiza esses secrets automaticamente.

### 2.1 Segundo apply via GitHub Actions (criar EC2)

Após popular os 7 secrets (database, rabbitmq, aws, clerk, newrelic, litellm, kong), troque a variável no workspace:

1. Terraform Cloud → workspace `archlens-ec2-deploy` → Variables → `bootstrap_services` = `true` → Save
2. GitHub → Actions → "Infra: Terraform Deploy" → Run workflow:
   - **action**: `plan` (revisar — o plano deve mostrar criação de `aws_instance.archlens[0]` e `aws_eip.archlens[0]`)
   - **action**: `apply`
   - **workspace**: `05-ec2-deploy`

Após esse apply:
- EC2 é criada e o user-data dispara automaticamente
- `bootstrap-rds.sh`, `fetch-secrets.sh`, `bootstrap-litellm-vk.sh` rodam encontrando secrets válidos
- Outputs `ec2_public_dns`, `frontend_url`, `kong_api_url` ficam preenchidos no summary

---

## Etapa 3 — Configurar GitHub Secrets

No repo → Settings → Secrets and variables → Actions:

### Secrets

| Nome | Valor |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user com permissão de ECR + SSM (ver abaixo) |
| `AWS_SECRET_ACCESS_KEY` | par do anterior |
| `EC2_HOST` | output `ec2_public_dns` do terraform — usado no health check final |
| `VITE_CLERK_PUBLISHABLE_KEY` | mesma chave do secret `archlens/$ENV/clerk` |

### Variables (não secrets)

| Nome | Valor |
|---|---|
| `VITE_CLERK_JWT_TEMPLATE` | `archlens` (opcional, default já é esse) |

### Permissões IAM do user do CI

O user da `AWS_ACCESS_KEY_ID` precisa ter (no mínimo):

- `AmazonEC2ContainerRegistryPowerUser` — pra build/push das imagens
- Permissão pra `ssm:SendCommand`, `ssm:GetCommandInvocation`, `ec2:DescribeInstances` — pra disparar o `deploy.sh` na EC2 via SSM

Policy customizada mínima:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:SendCommand",
        "ssm:GetCommandInvocation",
        "ec2:DescribeInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

> Deploy **não usa SSH** — usa AWS SSM Run Command. Por isso `EC2_SSH_USER` e `EC2_SSH_KEY` não são mais secrets necessários. Se existirem do setup antigo, pode remover.

---

## Etapa 4 — Validar a 1ª boot da EC2

A EC2 foi criada no **2º apply** da Etapa 2.1. O `user-data.sh.tftpl` roda como root e executa em ordem:

1. Instala dependências do host: Docker Engine + Compose plugin, AWS CLI v2, git, jq, postgresql-client
2. Clona o repo em `/opt/archlens` e configura `git safe.directory`
3. Escreve `/opt/archlens/.bootstrap.env` (com `export`) — vars para os scripts (`AWS_REGION`, `RDS_HOST`, `ECR_REGISTRY`, etc.)
4. Login no ECR
5. Executa `bootstrap-rds.sh` → espera RDS, cria os 4 DBs e users (idempotente)
6. Executa `fetch-secrets.sh` → gera os 7 `.env` em `/opt/archlens/secrets/`
7. Descobre a tag mais recente no ECR. Se houver imagens publicadas:
   - `docker compose pull`
   - Sobe deps (rabbit, presidio, litellm)
   - `ensure-rabbit-user.sh` → cria/atualiza user do RabbitMQ (necessário porque `management.load_definitions` não cria via env vars)
   - Espera litellm em `/health/liveliness`
   - `bootstrap-litellm-vk.sh` → gera Virtual Keys e atualiza secrets `processing` e `report` no Secrets Manager
   - `fetch-secrets.sh` (re-run) → puxa secrets já com `LLM_API_KEY`
   - `docker compose up -d` (services + frontend + kong + migrations)

   Se o ECR ainda estiver vazio (nenhum build feito), o user-data termina sem subir containers — você precisa disparar o workflow `EC2: Build & Deploy` primeiro (Etapa 5).
8. Trap final: `chown -R ubuntu:ubuntu /opt/archlens` + `chmod +x` nos scripts (roda mesmo se algum passo falhar, garantindo que SSH/SSM como `ubuntu` funcione)

Tempo total: ~5–10 min na 1ª boot.

### Acompanhar via SSM Session Manager

AWS Console → EC2 → Instance `archlens-ec2` → Connect → **Session Manager** → Connect

```bash
# Trocar do ssm-user para ubuntu (dono de /opt/archlens)
sudo -i -u ubuntu

# Logs do bootstrap
sudo tail -f /var/log/archlens-bootstrap.log

# Status dos containers
docker compose -f /opt/archlens/docker-compose.ec2.yml ps
```

### Validação externa

```bash
# Pega o DNS público (output do terraform ou via SSM)
curl http://<ec2_public_dns>/health                  # nginx do frontend
curl http://<ec2_public_dns>:8000/upload/health      # Kong → upload-service
```

Acessar no navegador: `http://<ec2_public_dns>` — abre a SPA do ArchLens. Fluxo end-to-end: faça upload de um diagrama, acompanhe o status, baixe o relatório (markdown buscado direto do S3 via presigned URL, com CORS já configurado).

### Acesso à UI do LiteLLM (operação)

A porta 4000 é exposta **somente para o `allowed_ssh_cidr`** (mesma restrição do SSH). Abrir no navegador:

```
http://<ec2_public_dns>:4000/ui
```

Login: cole o valor de `MASTER_KEY` do secret `archlens/<env>/litellm`.

---

## Etapa 5 — Deploys subsequentes

Apenas dispare o workflow no GitHub Actions:

**Actions → "EC2: Build & Deploy" → Run workflow → services: `all`**

Fluxo automático:
1. Build & push das 5 imagens (`archlens-ec2/upload-service:<commit-sha>`, etc.)
2. Descobre Instance ID via tag `Name=archlens-ec2` e dispara `deploy.sh <commit-sha>` via **AWS SSM Run Command** (sem SSH)
3. `deploy.sh` na EC2 faz: `git checkout`, re-fetch secrets, `docker compose pull`, sobe deps (rabbit/presidio/litellm), garante VKs, roda migrations, `up -d`
4. Health check em `/health` (frontend) e `:8000/upload/health` (Kong → upload)

**Update granular:** preencha `services` com CSV (ex: `upload-service,frontend`) para builder apenas esses.

> **Importante:** `deploy.sh` **não recria** EC2, RDS, RabbitMQ ou LiteLLM. Apenas atualiza imagens dos services e frontend. RDS continua intocado entre deploys.

---

## Custos estimados (us-east-2)

| Recurso | Custo mensal aproximado |
|---|---|
| EC2 t3.large **Spot** (persistent + stop, 24/7) | ~$18 |
| EBS gp3 50GB | ~$4 |
| Elastic IP (em uso) | $0 |
| RDS db.t4g.micro + 20GB gp2 | ~$15 |
| S3 (uso baixo) | <$1 |
| ECR (5 imagens × ~500MB × 5 versões) | ~$1 |
| Secrets Manager (9 secrets) | ~$3.60 |
| Data transfer | variável |
| **Total** | **~$43/mês** |

Custo é minimizado por dois fatores: sem NAT Gateway (RDS em subnet privada
sem necessidade de saída para internet; ~$32/mês economizados) e EC2 em Spot
em vez de On-Demand (~$42/mês economizados).

### Spot Instance — comportamento na interrupção

Configurada como `persistent` + `stop on interruption`:

- AWS reclama a capacidade → instância é **parada** (não terminada)
- EBS root é **preservado** (containers e configs intactos)
- Quando capacidade volta → instância **reinicia automaticamente**
- Containers retomam sozinhos (compose tem `restart: unless-stopped`)
- Elastic IP **mantém o DNS público** durante o ciclo

Para forçar On-Demand (zero risco de interrupção), setar no workspace:
```
ec2_use_spot = false
```

Custo extra: ~$42/mês.

---

## Destruir a infra

GitHub → Actions → **"Infra: Terraform Deploy"** → Run workflow → **action: `destroy`**.

Isso remove EC2, EIP, RDS, S3, ECR, Secrets Manager, VPC e demais recursos do stack. **RDS e S3 perdem dados** (`skip_final_snapshot = true`, sem versioning).

Para zerar parcialmente sem destruir a infra: setar `bootstrap_services = false` no workspace e dar apply — destrói só a EC2 + EIP, preserva RDS/S3/Secrets.

---

## Arquivos do stack

```
infra/terraform/05-ec2-deploy/
   main.tf, variables.tf, outputs.tf
   vpc.tf, rds.tf, s3.tf, ecr.tf
   ec2.tf, security-groups.tf, iam.tf, iam-newrelic.tf
   secrets.tf, user-data.sh.tftpl

infra/scripts/ec2/
   bootstrap-rds.sh          cria 4 DBs + 4 users no RDS (psql)
   fetch-secrets.sh          Secrets Manager → /opt/archlens/secrets/*.env
   ensure-rabbit-user.sh     cria/atualiza user do RabbitMQ via rabbitmqctl
   bootstrap-litellm-vk.sh   gera Virtual Keys do LiteLLM e atualiza secrets
   deploy.sh                 update in-place chamado pelo GH Actions via SSM

infra/scripts/rabbitmq/
   definitions.json          exchanges, queues, bindings (sem users — vêm do env)
   rabbitmq.conf             management.load_definitions

frontend/
   nginx.conf                config para dev local (proxy /s3 → localstack)
   nginx.ec2.conf            config para EC2 (sem /s3, CSP libera S3 + NR Browser)
   Dockerfile                aceita ARG NGINX_CONF para selecionar

.github/workflows/
   infra-deploy.yaml         plan/apply/destroy do Terraform via Actions
   ec2-deploy.yaml           build matrix (5 imagens) + SSM Run Command

docker-compose.ec2.yml       compose de produção (sem postgres/localstack/vault;
                             imagens vêm do ECR via ${IMAGE_TAG})
```
