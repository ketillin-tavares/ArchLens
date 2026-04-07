# Upload Service - ArchLens

Microsserviço responsável pelo ponto de entrada da plataforma ArchLens. Recebe diagramas de arquitetura via upload de arquivo, valida, armazena em S3 e orquestra o fluxo de análise assíncrona através de eventos RabbitMQ.

## Descrição do Serviço

O **Upload Service** é a porta de acesso para submissão de diagramas arquiteturais (PNG, JPEG, PDF). Ele implementa validação de arquivo, persistência em storage distribuído e publicação de eventos para processamento assíncrono pelos demais serviços (Processing Service e Report Service). O serviço segue **Clean Architecture** com rigorosa separação em camadas: Domain, Application, Interface Adapters e Infrastructure, utilizando o padrão **Ports & Adapters** para máximo desacoplamento e testabilidade.

## Estrutura de Diretórios

```
src/
├── domain/                                  # Camada de Domínio (regras de negócio puras)
│   ├── entities/
│   │   ├── diagrama.py                      # Entidade Diagrama (arquivo enviado)
│   │   └── analise.py                       # Entidade Análise (rastreamento de status)
│   ├── value_objects/
│   │   ├── arquivo_diagrama.py              # VO para validação e propriedades de arquivo
│   │   ├── status_analise.py                # VO enum com máquina de estados de status
│   │   └── storage_path.py                  # VO para caminho em storage
│   ├── repositories/                        # Ports (interfaces abstratas)
│   │   ├── diagrama_repository.py           # Contrato para persistência de diagramas
│   │   └── analise_repository.py            # Contrato para persistência de análises
│   ├── events.py                            # Eventos de domínio (DiagramaEnviado, etc)
│   ├── exceptions.py                        # Exceções de domínio customizadas
│   └── __init__.py
│
├── application/                             # Camada de Casos de Uso
│   ├── use_cases/
│   │   ├── submit_diagram.py                # Submete diagrama para análise
│   │   ├── get_analysis_status.py           # Consulta status de análise
│   │   ├── download_relatorio.py            # Gera URL para download do relatório
│   │   ├── retry_analysis.py                # Retenta análise com falha
│   │   ├── handle_status_update.py          # Handler de eventos de status
│   │   └── __init__.py
│   ├── ports/                               # Ports (interfaces para infraestrutura)
│   │   ├── event_publisher.py               # Contrato para publicar eventos
│   │   ├── file_storage.py                  # Contrato para armazenamento de arquivos
│   │   └── __init__.py
│   ├── dtos/                                # Data Transfer Objects
│   │   ├── diagrama_upload_response.py      # Resposta de upload
│   │   ├── analise_response.py              # Resposta de status
│   │   ├── download_relatorio_response.py   # Resposta com URL pré-assinada
│   │   └── __init__.py
│   └── __init__.py
│
├── interface/                               # Camada de Interface Adapters
│   ├── controllers/
│   │   ├── v1/
│   │   │   ├── analise_controller.py        # Rotas v1: POST/GET/PATCH análises
│   │   │   └── __init__.py
│   │   ├── health_controller.py             # Health check endpoint
│   │   └── __init__.py
│   ├── gateways/                            # Adapters (implementações concretas dos Ports)
│   │   ├── diagrama_repository_gateway.py   # SQLAlchemy para Diagrama
│   │   ├── analise_repository_gateway.py    # SQLAlchemy para Análise
│   │   ├── event_publisher_gateway.py       # RabbitMQ para publicação
│   │   ├── file_storage_gateway.py          # S3/MinIO para armazenamento
│   │   └── __init__.py
│   ├── presenters/
│   │   ├── error_presenter.py               # Modelos de erro HTTP
│   │   ├── health_presenter.py              # Modelo de health check
│   │   └── __init__.py
│   └── __init__.py
│
├── infrastructure/                          # Camada de Frameworks & Drivers
│   ├── database/
│   │   ├── session.py                       # Factory de sessões async SQLAlchemy
│   │   └── __init__.py
│   ├── models/
│   │   ├── base.py                          # Classe base declarativa
│   │   ├── diagrama_model.py                # Mapeamento ORM para Diagrama
│   │   ├── analise_model.py                 # Mapeamento ORM para Análise
│   │   └── __init__.py
│   ├── messaging/
│   │   ├── publisher.py                     # Publicador de eventos RabbitMQ
│   │   ├── consumer.py                      # Consumidor de eventos (status updates)
│   │   ├── shared.py                        # Instância global de publisher
│   │   └── __init__.py
│   ├── storage/
│   │   ├── s3_client.py                     # Client aioboto3 para S3/MinIO
│   │   └── __init__.py
│   ├── observability/
│   │   ├── logging.py                       # Configuração loguru com contexto
│   │   ├── metrics.py                       # Recorder de métricas New Relic
│   │   ├── tracing.py                       # Tracing distribuído
│   │   └── __init__.py
│   ├── alembic/
│   │   ├── env.py                           # Configuração de migrações
│   │   ├── versions/                        # Scripts de versionamento
│   │   └── alembic.ini
│   └── __init__.py
│
├── environment.py                           # Configurações (Pydantic Settings)
├── main.py                                  # Aplicação FastAPI principal
└── __init__.py

tests/
├── test_domain/
│   ├── test_entities.py                     # Testes de Diagrama e Análise
│   ├── test_value_objects.py                # Testes de validação
│   ├── test_events.py                       # Testes de eventos de domínio
│   └── __init__.py
├── test_application/
│   ├── test_use_cases.py                    # Testes de casos de uso
│   └── __init__.py
├── test_interface/
│   ├── test_controllers.py                  # Testes de endpoints HTTP
│   ├── test_gateways.py                     # Testes de adapters
│   ├── test_health_controller.py            # Testes de health check
│   └── __init__.py
├── test_infrastructure/
│   ├── test_storage.py                      # Testes de S3
│   ├── test_messaging.py                    # Testes de RabbitMQ
│   ├── test_observability.py                # Testes de logging/métricas
│   └── __init__.py
├── test_main.py                             # Testes de integração
└── __init__.py
```

## Arquitetura

O projeto implementa **Clean Architecture** com inversão de dependências via **Ports & Adapters**

## Setup Local

### Pré-requisitos

- **Python** 3.13+
- **UV** (gerenciador de pacotes)
- **Docker & Docker Compose** (para infraestrutura local)

### Instalação de Dependências

```bash
cd services/upload-service

# Instalar UV (se não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependências (produção + desenvolvimento)
uv sync
```

### Configuração de Ambiente

```bash
# Copiar variáveis de exemplo
cp env.example .env

# Editar .env com valores locais se necessário
# (valores padrão em env.example já funcionam com docker-compose)
```

### Rodando a Infraestrutura

Na raiz do projeto ArchLens, inicie a infraestrutura compartilhada:

```bash
docker compose up -d

# Aguarde alguns segundos para estabilização
docker compose ps
```

Isto inicia: PostgreSQL, RabbitMQ, LocalStack (S3), Vault, Kong, New Relic Agent, etc.

### Inicializando o Serviço

#### Bare Metal (Desenvolvimento)

```bash
# Aplicar migrações do banco
uv run alembic upgrade head

# Iniciar servidor com auto-reload
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse em `http://localhost:8000`.

#### Docker

```bash
# Build da imagem (multistage: builder + runtime)
docker build -t archlens-upload-service:latest .

# Rodar container
docker run --env-file .env -p 8000:8000 archlens-upload-service:latest
```

### Verificar Saúde

```bash
curl http://localhost:8000/health
```

Resposta esperada:
```json
{
  "status": "ok",
  "timestamp": "2026-04-07T10:15:30Z"
}
```

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do serviço (use `env.example` como base):

### Banco de Dados PostgreSQL

```bash
DATABASE_HOST=postgres              # Host do PostgreSQL
DATABASE_PORT=5432                  # Porta
DATABASE_USER=upload_user           # Usuário
DATABASE_PASSWORD=upload_pass       # Senha
DATABASE_NAME=upload_db             # Nome do banco
```

### RabbitMQ

```bash
RABBITMQ_HOST=rabbitmq              # Host do RabbitMQ
RABBITMQ_PORT=5672                  # Porta AMQP
RABBITMQ_USER=archlens              # Usuário
RABBITMQ_PASSWORD=archlens_dev      # Senha
RABBITMQ_EXCHANGE_NAME=analise.events           # Exchange para publicação
RABBITMQ_QUEUE_NAME=upload-service.status-updates  # Fila de consumo
```

### S3

```bash
S3_ENDPOINT_URL=http://localstack:4566  # Endpoint S3
AWS_ACCESS_KEY_ID=test              # Access key (LocalStack)
AWS_SECRET_ACCESS_KEY=test          # Secret key (LocalStack)
S3_BUCKET_NAME=archlens-diagramas   # Nome do bucket
AWS_REGION=us-east-1                # Região
```

### Aplicação

```bash
SERVICE_NAME=upload-service         # Nome do serviço
DEBUG=false                         # Modo debug (false em prod)
LOG_LEVEL=INFO                      # Nível de log
```

### New Relic (Observabilidade)

```bash
NEW_RELIC_USER_KEY=<sua_chave>      # User API key
NEW_RELIC_LICENSE_KEY=<sua_chave>   # License key
NEW_RELIC_ACCOUNT_ID=<seu_account>  # Account ID
NRIA_DISPLAY_NAME=upload-service    # Nome no dashboard
NRIA_LICENSE_KEY=<sua_chave>        # License key para agent
```

## Endpoints da API

### POST /v1/analises

Submete um diagrama de arquitetura para análise.

**Request:**
- Multipart form-data com campo `file`
- Tipos aceitos: `image/png`, `image/jpeg`, `application/pdf`
- Tamanho máximo: 10 MB

**Response (202 Accepted):**
```json
{
  "analise_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "recebido",
  "criado_em": "2026-04-07T10:15:30Z"
}
```

**Erros:**
- `400 Bad Request`: Tipo de arquivo não suportado
- `413 Payload Too Large`: Arquivo excede 10 MB

**Exemplo:**
```bash
curl -X POST http://localhost:8000/v1/analises \
  -F "file=@diagrama.png"
```

---

### GET /v1/analises/{analise_id}

Consulta o status de uma análise.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "diagrama_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "em_processamento",
  "erro_detalhe": null,
  "relatorio_s3_key": null,
  "criado_em": "2026-04-07T10:15:30Z",
  "atualizado_em": "2026-04-07T10:16:00Z"
}
```

**Erros:**
- `404 Not Found`: Análise não encontrada

**Exemplo:**
```bash
curl http://localhost:8000/v1/analises/550e8400-e29b-41d4-a716-446655440000
```

---

### GET /v1/analises/{analise_id}/relatorio/download

Gera URL pré-assinada para download do relatório Markdown. A análise deve estar com status `analisado`. URL expira em 3600 segundos.

**Response (200 OK):**
```json
{
  "download_url": "https://s3.archlens.local/archlens-diagramas/...",
  "expira_em": 3600
}
```

**Erros:**
- `404 Not Found`: Análise não encontrada
- `409 Conflict`: Análise não concluída ou relatório não disponível

**Exemplo:**
```bash
curl http://localhost:8000/v1/analises/550e8400-e29b-41d4-a716-446655440000/relatorio/download
```

---

### POST /v1/analises/{analise_id}/retry

Retenta o processamento de uma análise que falhou (status `erro`).

**Response (202 Accepted):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "diagrama_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "recebido",
  "erro_detalhe": null,
  "criado_em": "2026-04-07T10:15:30Z",
  "atualizado_em": "2026-04-07T10:16:30Z"
}
```

**Erros:**
- `404 Not Found`: Análise não encontrada
- `409 Conflict`: Análise não está em estado de erro

**Exemplo:**
```bash
curl -X POST http://localhost:8000/v1/analises/550e8400-e29b-41d4-a716-446655440000/retry
```

---

### GET /health

Health check que valida conexões com dependências (BD, RabbitMQ, S3).

**Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2026-04-07T10:15:30Z"
}
```

**Exemplo:**
```bash
curl http://localhost:8000/health
```

## Testes e QA

### Executar Testes Unitários

```bash
# Todos os testes com cobertura
uv run pytest --cov=src --cov-report=term-missing

# Apenas um módulo
uv run pytest tests/test_domain/ -v

# Com output detalhado
uv run pytest -v --tb=short
```

### Linting e Formatação de Código

```bash
# Verificar estilo com Ruff
uv run ruff check src/ tests/

# Formatar automaticamente
uv run ruff format src/ tests/

# Type checking (validação de tipos)
uv run ty check src/
```

### Quality Gate Completo

```bash
# Executar format, lint, type check e testes
make quality

# Ou manualmente:
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
uv run ty check src/
uv run pytest --cov=src --cov-report=term-missing
```

### Pre-commit Hooks

```bash
# Instalar hooks (rodam antes de cada commit)
uv run pre-commit install

# Executar manualmente em todos os arquivos
uv run pre-commit run --all-files
```

## Docker

### Dockerfile Multistage

O `Dockerfile` utiliza construção em múltiplas etapas para minimizar o tamanho final:

**Stage 1 (Builder)**: Compila dependências com UV
**Stage 2 (Runtime)**: Copia apenas artefatos necessários

```dockerfile
FROM python:3.13-slim AS builder
  # Instala UV e compila dependências

FROM python:3.13-slim AS runtime
  # Copia apenas .venv do builder
```

### Build

```bash
docker build -t archlens-upload-service:latest .
```

### Execução

```bash
# Com arquivo .env
docker run --env-file .env -p 8000:8000 archlens-upload-service:latest

# Com variáveis inline
docker run \
  -e DATABASE_HOST=postgres \
  -e RABBITMQ_HOST=rabbitmq \
  -p 8000:8000 \
  archlens-upload-service:latest
```

### Via Docker Compose

Na raiz do projeto ArchLens:

```bash
# Subir todos os serviços
docker compose up -d

# Parar
docker compose down

# Logs do upload-service
docker compose logs -f upload-service
```

## Estrutura de Dados

### Tabela `diagramas`

```sql
CREATE TABLE diagramas (
  id UUID PRIMARY KEY,
  nome_original VARCHAR(255),
  content_type VARCHAR(50),
  tamanho_bytes INTEGER,
  storage_path VARCHAR(512),
  criado_em TIMESTAMP
);
```

### Tabela `analises`

```sql
CREATE TABLE analises (
  id UUID PRIMARY KEY,
  diagrama_id UUID REFERENCES diagramas(id),
  status VARCHAR(50),
  erro_detalhe TEXT,
  relatorio_s3_key VARCHAR(512),
  criado_em TIMESTAMP,
  atualizado_em TIMESTAMP
);
```

## Observabilidade

### Logging

Utiliza `loguru` com logs estruturados:

```python
from src.infrastructure.observability.logging import get_logger

logger = get_logger()
logger.info("diagrama_recebido", analise_id=str(analise.id), tamanho_bytes=tamanho)
```

### Métricas

New Relic integration para monitoring:
- `analise_por_status`: Contagem por status
- `falha_processamento`: Contagem de falhas

### Tracing Distribuído

Suporte a tracing com headers:
- `traceparent`
- `newrelic`

## Recursos Adicionais

- **Validação**: Pydantic com type hints obrigatórios
- **Resiliência**: Circuit breaker (pybreaker), retry com backoff (tenacity)
- **Segurança**: Multipart validation, validação de MIME types
- **Performance**: Processamento assíncrono (asyncio), database connection pooling

## Padrões de Código

### Clean Code

- Nomes descritivos que revelam intenção
- Funções com responsabilidade única
- Type hints em argumentos e retornos
- Docstrings em todas as funções públicas

### Proibições

- **Nunca** use `print()` — use `logger` (loguru)
- **Nunca** importe dentro de funções — imports sempre no topo
- **Nunca** crie funções aninhadas — extraia para métodos
- **Nunca** misture camadas — use Ports & Adapters

### Naming Conventions

- Classes: `PascalCase` (ex: `SubmitDiagram`)
- Funções/variáveis: `snake_case` (ex: `validar_arquivo`)
- Constantes: `UPPERCASE_WITH_UNDERSCORES` (ex: `TAMANHO_MAXIMO_BYTES`)

## Suporte

Para dúvidas, consulte a documentação do projeto principal (ArchLens) ou entre em contato com a equipe de arquitetura.
