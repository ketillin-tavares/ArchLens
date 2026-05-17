# ArchLens

| Serviço | Quality Gate |
|---------|:------------:|
| Processing Service | [![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=archlens_archlens-processing-service)](https://sonarcloud.io/summary/new_code?id=archlens_archlens-processing-service) |
| Upload Service | [![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=archlens_archlens-upload-service)](https://sonarcloud.io/summary/new_code?id=archlens_archlens-upload-service) |
| Report Service | [![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=archlens_archlens-report-service)](https://sonarcloud.io/summary/new_code?id=archlens_archlens-report-service) |
| Frontend | [![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=archlens_archlens-frontend)](https://sonarcloud.io/summary/new_code?id=archlens_archlens-frontend) |

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

## O Problema

Empresas com sistemas distribuídos acumulam dezenas de diagramas de arquitetura (imagens/PDFs) usados em revisões de design, auditorias de segurança, avaliações de escalabilidade e discussões técnicas. A análise manual é lenta, depende de especialistas e não escala. O **ArchLens** automatiza a análise técnica inicial desses artefatos através de um pipeline LLM multi-agente com guardrails de segurança.

## Arquitetura

Todos os serviços de aplicação seguem **Clean Architecture** com implementação obrigatória de Ports & Adapters.

### Componentes Principais

| Serviço | Responsabilidade | Porta Local |
|---------|-----------------|-------------|
| Frontend | SPA React + Vite, autenticação Clerk | 8091 |
| Kong Gateway | Proxy reverso, rate-limiting, CORS, autenticação JWT | 8000 |
| Upload Service | Recebe uploads, armazena no S3, publica evento de análise | 8010 |
| Processing Service | Consome evento, executa pipeline LLM multi-agente com guardrails | 8011 |
| Report Service | Consome resultado do processamento, gera relatório Markdown | 8012 |
| LiteLLM Gateway | Proxy LLM com guardrails (PII, JSON validator, prompt injection), cache e virtual keys | 4000 |
| RabbitMQ | Message broker para orquestração assíncrona | 5672 / 15672 |
| PostgreSQL | Banco relacional (4 bancos lógicos isolados) | 5432 |
| LocalStack | Emulação AWS S3 para armazenamento | 4566 |
| Presidio Analyzer | Detecção de PII | 5001 |
| Presidio Anonymizer | Anonimização de PII | 5002 |
| New Relic Infrastructure | Coleta de métricas e logs | — |

### Diagramas de Arquitetura

- **C1 (Contexto) e C2 (Containers):** disponíveis no Miro — **[Ver no Miro](https://miro.com/app/board/uXjVHSGO7qY=/?share_link_id=805394473514)**
- **C3 (Componentes):** diagramas Mermaid por serviço em [docs/diagrams/](docs/diagrams/)
  - [c3-upload-service.mmd](docs/diagrams/c3-upload-service.mmd)
  - [c3-processing-service.mmd](docs/diagrams/c3-processing-service.mmd)
  - [c3-report-service.mmd](docs/diagrams/c3-report-service.mmd)

### Nota sobre banco de dados (MVP)

Uma única instância RDS é compartilhada entre todos os serviços (cada um usa seu próprio banco de dados lógico dentro da mesma instância). Em produção real, cada microsserviço teria sua própria instância dedicada, respeitando o princípio _database per service_.

## Fluxo da Solução

1. **Upload inicial:** Usuário faz upload do diagrama via Frontend → Kong → Upload Service
   - Salva arquivo no S3 (LocalStack/AWS)
   - Cria registro no PostgreSQL com status `RECEBIDO`
   - Publica evento `analise.diagrama.enviado` no RabbitMQ

2. **Processamento assíncrono:** Processing Service consome o evento
   - Baixa diagrama do S3
   - Se PDF: converte para imagem via PyMuPDF
   - Executa pipeline LLM via LiteLLM Gateway:
     - **Guardrail pré-chamada:** Presidio mascara PII
     - **Agent Extractor:** identifica componentes do diagrama
     - **Agent Analyzer:** analisa riscos arquiteturais
     - **Agent Judge:** valida e corrige output
     - **Guardrail pós-chamada:** JSON response validator
   - Salva resultado no PostgreSQL
   - Publica `analise.processamento.concluida` no RabbitMQ

3. **Geração de relatório:** Report Service consome `analise.processamento.concluida`
   - Gera relatório Markdown via LiteLLM
   - Armazena `.md` no S3
   - Publica `analise.relatorio.gerado`

4. **Atualização de status:** Upload Service consome eventos (iniciado, concluída, relatório gerado, falhou) e atualiza registro

5. **Consulta de resultados:** Frontend faz polling em `GET /v1/analises/{id}` para acompanhar status
   - Download presigned: `GET /v1/analises/{id}/relatorio/download`
   - Estruturado: `GET /v1/relatorios/{id}`

## Stack Técnica

### Backend (3 serviços)
- **Linguagem/Framework:** Python 3.13, FastAPI
- **Banco de dados:** SQLAlchemy 2.0 (async), asyncpg, Alembic migrations
- **IA/LLM:** PydanticAI + LiteLLM (Gemini 3.1 Flash Lite Preview, fallback Gemini 2.5 Flash)
- **Mensageria:** aio-pika (RabbitMQ)
- **Armazenamento:** aioboto3 (S3)
- **Validação:** Pydantic
- **Logging:** Loguru
- **Observabilidade:** New Relic APM
- **Processamento:** PyMuPDF, Pillow

### Frontend
- **Framework:** React 18.3 + TypeScript 5.6
- **Build:** Vite 5.4
- **Autenticação:** Clerk
- **HTTP:** Axios
- **Server:** Nginx 1.27

### Infraestrutura
- **Containerização:** Docker (multistage builds), Docker Compose
- **IaC:** Terraform (AWS: EC2, RDS, ECR, VPC, IAM)
- **Proxy/API Gateway:** Kong 3.9 (DB-less, declarativo)
- **Proxy LLM:** LiteLLM com guardrails
- **Detecção PII:** Presidio
- **S3 (dev):** LocalStack / AWS (prod)

### CI/CD e Qualidade
- **CI/CD:** GitHub Actions
- **Code Quality:** SonarCloud
- **Lint/Format:** Ruff (com auto-fix)
- **Gerenciador Deps:** uv
- **Pre-commit hooks:** ruff, terraform_fmt, hadolint, actionlint

## Execução e Deploy

### Ambiente Local

Para setup completo do ambiente local (Docker Compose), consulte:

📄 **[docs/local.md](docs/local.md)**

### AWS (Produção)

Para deploy em EC2 com Terraform e CI/CD, consulte:

📄 **[docs/deploy_ec2_guide.md](docs/deploy_ec2_guide.md)**

### Pontos Críticos

#### ⚠️ Chave Clerk

O `docker-compose.yml` contém um valor padrão codificado para `VITE_CLERK_PUBLISHABLE_KEY`. **Antes de commitar qualquer alteração nesse arquivo, substitua esse valor por um placeholder** (ex.: `pk_test_REPLACE_ME`) ou remova o default.

Para rodar o ambiente, obtenha sua chave publicável de desenvolvimento no [Clerk Dashboard](https://dashboard.clerk.com) e defina `VITE_CLERK_PUBLISHABLE_KEY` no arquivo `.env` local (referenciado no `env.example`).

#### Painel Web LiteLLM

Acessar em `http://localhost:4000`. A master key é definida pela variável `LITELLM_MASTER_KEY` no arquivo `.env` local — consulte `env.example` para referência.

#### Portas Principais

- **Frontend:** http://localhost:8091
- **Kong (proxy da API):** http://localhost:8000
- **Kong Admin GUI:** http://localhost:8002
- **LiteLLM (UI + API):** http://localhost:4000
- **RabbitMQ Management:** http://localhost:15672
- **Services (acesso direto):**
  - Upload: http://localhost:8010
  - Processing: http://localhost:8011
  - Report: http://localhost:8012
- **LocalStack S3:** http://localhost:4566

## Endpoints Principais

Todos acessíveis via Kong Gateway em `http://localhost:8000`.

### Upload Service (`/v1/analises`)

- `POST /v1/analises` — envia diagrama (multipart/form-data), retorna 202 Accepted
- `GET /v1/analises/{analise_id}` — consulta status e detalhes
- `GET /v1/analises/{analise_id}/relatorio/download` — URL presigned S3 para download
- `POST /v1/analises/{analise_id}/retry` — retenta análise com erro

### Report Service (`/v1/relatorios`)

- `GET /v1/relatorios/{analise_id}` — relatório estruturado (componentes, riscos, recomendações)

### Processing Service (`/v1/processamentos`)

- `GET /v1/processamentos/{analise_id}` — resultado bruto do processamento (debug)

### Health Checks

- `GET /upload` — Upload Service
- `GET /processing` — Processing Service
- `GET /health` — Report Service

## Testes Manuais — Postman

A pasta [docs/postman/](docs/postman/) contém duas collections e três environments prontos para importar no Postman.

### Collections

| Arquivo | Ambiente alvo |
|---------|---------------|
| [archlens-collection.json](docs/postman/archlens-collection.json) | Local (Docker Compose) |
| [archlens-collection-deployed.json](docs/postman/archlens-collection-deployed.json) | Deployed (AWS EC2) |

A collection local cobre o fluxo completo incluindo acesso direto aos serviços e infraestrutura. A collection deployed expõe apenas os endpoints publicamente acessíveis na EC2: health checks, upload de diagrama, polling de status, consulta de processamento, consulta de relatório, download presigned e testes de erro (400, 404, 409, 413).

### Environments

| Arquivo | Uso |
|---------|-----|
| [environment-kong-gateway.json](docs/postman/environment-kong-gateway.json) | Local — via Kong (porta 8000) |
| [environment-direct-access.json](docs/postman/environment-direct-access.json) | Local — acesso direto aos serviços (portas 8010/8011/8012) |
| [environment-kong-deployed.json](docs/postman/environment-kong-deployed.json) | Deployed — Kong na EC2 |

### Como usar

1. No Postman: **Import** → selecione a collection e o environment desejados.
2. Para o ambiente **local**: ative `ArchLens - Kong Gateway` ou `ArchLens - Acesso Direto`.
3. Para o ambiente **deployado**:
   - Ative `ArchLens - Kong Gateway (Deployed - AWS)`.
   - Preencha `base_url` com o valor de `terraform output kong_api_url` (formato: `http://<EC2_PUBLIC_DNS>:8000`).
   - Se o Kong JWT estiver habilitado, gere o token com `python gateways/kong/generate-jwt.py` e preencha `kong_jwt_token`.
4. Execute o grupo **Fluxo Completo (Happy Path)** na ordem — o `analise_id` é salvo automaticamente entre as requests.

> Na EC2, apenas as portas 8000 (Kong) e 4000 (LiteLLM — restrito ao IP do operador) são expostas publicamente. Acesso direto aos serviços (8010/8011/8012), RabbitMQ Management e Kong Admin não estão disponíveis externamente.

## Testes

Execute via Makefile em cada serviço:

```bash
# Upload Service
cd services/upload-service
make test-cov

# Processing Service (unitários — sem chamada real ao LLM)
cd services/processing-service
make test-cov

# Testes de integração (requer GEMINI_API_KEY):
uv run pytest -m integration

# Report Service
cd services/report-service
make test-cov
```

Todos os testes unitários usam mock das interfaces (ports) — nunca acessam banco ou serviços externos.

## CI/CD

### SonarCloud (sonarcloud.yaml)

Dispara em push para `main` ou manualmente:
1. Detecta serviços alterados (dorny/paths-filter)
2. Executa `pytest --cov` em matrix para cada serviço Python
3. Envia cobertura ao SonarCloud (org `archlens`)
4. Analisa frontend

### Deploy EC2 (ec2-deploy.yaml)

Dispara manualmente (workflow_dispatch):
1. Autentica na AWS via OIDC
2. Build Docker multistage + push para ECR (tag = SHA do commit)
3. SSM Send Command à instância EC2 para executar script de deploy

**Serviços:** upload, processing, report, litellm, frontend (em paralelo)

### Infraestrutura (infra-deploy.yaml)

Dispara manualmente:
- Plan/Apply via Terraform Cloud (workspace `archlens-ec2-deploy`)
- Provisiona: VPC, EC2, RDS, ECR, IAM, integração New Relic

## Observabilidade

New Relic é a plataforma central de observabilidade:

- **Logs estruturados:** Loguru, coletados pelo New Relic Infrastructure Agent
- **APM:** Cada serviço Python roda sob `newrelic-admin run-program`
- **Métricas customizadas:** `AnaliseSucesso`, `AnaliseFalha`, tempo de pipeline, confiança da IA, profundidade de filas, volume de relatórios
- **21 condições de alerta NRQL:** taxa de erros, latência P95, DLQ, CPU/memória, confiança da IA, pipeline E2E
- **Dashboard com 7 páginas:** Visão Geral, Upload Service, Processing Service (AI), Report Service, Infraestrutura & Mensageria, Logs & Erros, AWS Infrastructure

📄 **[docs/newrelic/README.md](docs/newrelic/README.md)** — instruções de importação do dashboard e configuração dos alertas.

## Pre-commit Hooks

Hooks configurados no `.pre-commit-config.yaml`:
- `ruff` — linting e formatação Python (com auto-fix)
- `terraform_fmt` / `terraform_validate` — formatação e validação Terraform
- `hadolint` — linting de Dockerfiles
- `actionlint` — validação de GitHub Actions workflows
- Checks básicos: trailing whitespace, end-of-file, YAML válido, arquivos grandes (> 1MB)

### Instalação e Uso

```bash
pip install pre-commit
pre-commit install

# Executar manualmente em todos os arquivos
pre-commit run --all-files
```

## Estrutura de Pastas

```
ArchLens/
├── services/
│   ├── upload-service/          # FastAPI: recebe uploads e orquestra status
│   │   └── src/
│   │       ├── domain/          # Entidades, value objects, exceções, ports
│   │       ├── application/     # Use cases
│   │       ├── infrastructure/  # DB, S3, RabbitMQ, observabilidade
│   │       └── interface/       # Controllers FastAPI, gateways, presenters
│   ├── processing-service/      # FastAPI + PydanticAI: pipeline LLM multi-agente
│   │   └── src/ (mesma estrutura de camadas)
│   └── report-service/          # FastAPI + PydanticAI: geração de relatórios
│       └── src/ (mesma estrutura de camadas)
│
├── frontend/                    # React 18 + TypeScript + Vite + Clerk
│   └── src/
│       ├── pages/               # NewAnalysisPage, ResultsPage, SearchReportPage
│       ├── components/          # FileDrop, MarkdownRenderer, RiskCallout, SignInScreen
│       ├── services/            # analysisService, httpClient
│       └── hooks/               # useAnaliseStatus, useAuthSetup
│
├── gateways/
│   ├── kong/                    # Config declarativa: rotas, plugins, auth JWT
│   └── litellm/                 # Proxy LLM: guardrails, cache, virtual keys
│
├── infra/
│   ├── terraform/05-ec2-deploy/ # IaC: EC2, RDS, ECR, VPC, IAM, New Relic
│   └── scripts/                 # Init scripts: PostgreSQL, RabbitMQ, LocalStack
│
├── docs/
│   ├── local.md                 # Setup do ambiente local
│   ├── deploy_ec2_guide.md      # Deploy em produção na AWS
│   └── newrelic/                # Dashboard JSON, 21 alertas NRQL, README
│
├── .github/workflows/           # CI/CD: SonarCloud, deploy EC2, Terraform
├── docker-compose.yml           # Ambiente de desenvolvimento (19 serviços)
├── docker-compose.ec2.yml       # Compose para deploy na EC2
├── .pre-commit-config.yaml      # Hooks de qualidade
├── env.example                  # Referência de variáveis de ambiente
└── Makefile                     # Comandos utilitários
```

## Equipe

| Nome | Papel |
|------|-------|
| Ketillin Tavares | Engenheira de Software — desenvolvimento completo do projeto |

*Desenvolvido para o Hackathon Integrado SOAT/IADT — FIAP*
