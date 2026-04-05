# Upload Service

Ponto de entrada do ArchLens que recebe diagramas de arquitetura via upload, armazena em S3/MinIO e orquestra o fluxo de análise através de eventos publicados no RabbitMQ.

## Estrutura do Projeto

```
services/upload-service/
├── src/                                  # Código-fonte da aplicação
│   ├── domain/                          # Camada de Domínio (regras de negócio)
│   │   ├── entities.py                  # Entidades: Diagrama, Analise
│   │   ├── value_objects.py             # Value objects: ArquivoDiagrama, StatusAnalise
│   │   ├── events.py                    # Eventos de domínio: DiagramaEnviado
│   │   ├── exceptions.py                # Exceções customizadas de domínio
│   │   └── repositories.py              # Interfaces (Ports) de repositórios
│   │
│   ├── application/                     # Camada de Aplicação (casos de uso)
│   │   ├── use_cases.py                 # Cases de uso: SubmitDiagram, GetAnalysisStatus, HandleStatusUpdate
│   │   ├── dtos.py                      # Data Transfer Objects para entrada/saída
│   │   └── ports.py                     # Interfaces (Ports) de FileStorage e EventPublisher
│   │
│   ├── infrastructure/                  # Camada de Infraestrutura (detalhes técnicos)
│   │   ├── database/                    # Conexão e sessões SQLAlchemy async
│   │   │   ├── session.py               # Configuração de conexão async
│   │   │   └── __init__.py
│   │   ├── models/                      # Modelos SQLAlchemy (mapeamento de tabelas)
│   │   │   ├── base.py                  # Classe base para modelos
│   │   │   ├── tables.py                # Tabelas: DiagramaORM, AnaliseORM
│   │   │   └── __init__.py
│   │   ├── messaging/                   # RabbitMQ (pub/sub)
│   │   │   ├── publisher.py             # RabbitMQPublisher (conexão e publicação)
│   │   │   ├── consumer.py              # RabbitMQConsumer (escuta eventos de status)
│   │   │   ├── shared.py                # Instância global do publisher
│   │   │   └── __init__.py
│   │   ├── observability/               # Logging e métricas
│   │   │   ├── logging.py               # Configuração de logging estruturado
│   │   │   ├── metrics.py               # Métricas da aplicação
│   │   │   └── __init__.py
│   │   ├── storage/                     # Armazenamento em S3/MinIO
│   │   │   ├── s3_client.py             # Cliente boto3 async
│   │   │   └── __init__.py
│   │   ├── alembic/                     # Migrações de banco de dados
│   │   │   ├── versions/                # Scripts de migração
│   │   │   └── env.py                   # Configuração do Alembic
│   │   └── __init__.py
│   │
│   ├── interface/                       # Camada de Interface Adapters
│   │   ├── controllers/                 # Rotas HTTP (FastAPI)
│   │   │   ├── v1/                      # Versão 1 da API
│   │   │   │   ├── analise_controller.py    # Endpoints: POST /analises, GET /analises/{id}
│   │   │   │   └── __init__.py
│   │   │   ├── health_controller.py     # Health check
│   │   │   └── __init__.py
│   │   ├── gateways/                    # Implementações concretas (Adapters)
│   │   │   ├── diagrama_repository_gateway.py    # SQLAlchemy adapter para Diagrama
│   │   │   ├── analise_repository_gateway.py     # SQLAlchemy adapter para Analise
│   │   │   ├── event_publisher_gateway.py        # RabbitMQ adapter para pub/sub
│   │   │   ├── file_storage_gateway.py           # S3/MinIO adapter
│   │   │   └── __init__.py
│   │   ├── presenters/                  # Formatadores de resposta HTTP
│   │   │   ├── health_presenter.py
│   │   │   ├── error_presenter.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── environment.py                   # Configurações via Pydantic Settings
│   ├── main.py                          # Inicialização FastAPI, lifespan, exception handlers
│   └── __init__.py
│
├── tests/                               # Testes automatizados
│   ├── test_domain/                     # Testes de entidades e value objects
│   ├── test_application/                # Testes de casos de uso (mocks de Ports)
│   ├── test_interface/                  # Testes de controllers (integração HTTP)
│   └── __init__.py
│
├── pyproject.toml                       # Configuração do projeto (uv, pytest, ruff)
├── alembic.ini                          # Configuração das migrações
├── Dockerfile                           # Build multistage (builder + runtime)
├── docker-compose.yml                   # Orquestração local (app, DB, RabbitMQ, S3)
├── env.example                          # Variáveis de ambiente (template)
└── README.md                            # Este arquivo
```

## Pré-requisitos

- Python 3.13+
- Docker e Docker Compose
- uv (gerenciador de dependências)

## Configuração Local

### 1. Clonar o repositório e navegar até o serviço

```bash
cd services/upload-service
```

### 2. Preparar variáveis de ambiente

```bash
cp env.example .env
```

Edite o arquivo `.env` se desejar alterar as configurações padrão. As configurações padrão funcionam com o `docker-compose.yml` fornecido.

### 3. Instalar dependências

```bash
uv sync
```

Isso cria um ambiente virtual e instala as dependências de produção e desenvolvimento.

### 4. Rodar migrations do banco de dados

Se estiver usando banco de dados local (bare metal):

```bash
uv run alembic upgrade head
```

Se estiver usando Docker Compose, as migrações serão executadas automaticamente na inicialização.

### 5. Iniciar a aplicação

#### Opção A: Bare Metal

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

A aplicação estará disponível em `http://localhost:8000`.

#### Opção B: Docker Compose

```bash
docker-compose up -d
```

Isso inicia:
- **upload-service**: Porta 8000
- **PostgreSQL**: Porta 5432 (volume persistente)
- **RabbitMQ**: Porta 5672 (management UI na porta 15672)
- **LocalStack** (S3): Porta 4566

Para visualizar logs:

```bash
docker-compose logs -f upload-service
```

Para parar:

```bash
docker-compose down
```

## Testes e QA

### Executar testes

```bash
uv run pytest
```

Executar testes com cobertura:

```bash
uv run pytest --cov=src --cov-report=html
```

### Executar linter (ruff)

```bash
uv run ruff check src tests
```

Corrigir problemas de estilo automaticamente:

```bash
uv run ruff check src tests --fix
```

### Verificação de tipos (mypy)

```bash
uv run mypy src --strict
```

## Endpoints da API

### POST /v1/analises

Recebe um diagrama de arquitetura via upload e inicia o fluxo de análise.

**Request:**
- Multipart form-data com campo `file`
- Tipos suportados: `image/png`, `image/jpeg`, `application/pdf`
- Tamanho máximo: 10 MB

**Response (202 Accepted):**
```json
{
  "analise_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "recebido",
  "criado_em": "2026-03-30T10:15:30Z"
}
```

**Erros:**
- `400 Bad Request`: Tipo de arquivo não suportado
- `413 Payload Too Large`: Arquivo excede 10 MB

### GET /v1/analises/{analise_id}

Consulta o status de uma análise.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "diagrama_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "em_processamento",
  "erro_detalhe": null,
  "criado_em": "2026-03-30T10:15:30Z",
  "atualizado_em": "2026-03-30T10:16:00Z"
}
```

**Erros:**
- `404 Not Found`: Análise não encontrada

### GET /v1/analises/{analise_id}/relatorio/download

Gera URL pré-assinada para download do relatório Markdown. A análise deve estar com status 'analisado'. A URL expira em 3600 segundos.

**Response (200 OK):**
```json
{
  "download_url": "https://s3.archlens.local/archlens-diagramas/analise-550e8400.md?...",
  "expira_em": 3600
}
```

**Erros:**
- `404 Not Found`: Análise não encontrada
- `409 Conflict`: Análise não concluída ou relatório ainda não gerado

### POST /v1/analises/{analise_id}/retry

Retenta o processamento de uma análise com status 'erro'.

**Response (202 Accepted):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "diagrama_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "recebido",
  "erro_detalhe": null,
  "criado_em": "2026-03-30T10:15:30Z",
  "atualizado_em": "2026-03-30T10:16:00Z"
}
```

**Erros:**
- `404 Not Found`: Análise não encontrada
- `409 Conflict`: Estado inválido para retry (apenas status 'erro' pode ser retentado)

### GET /health

Health check que valida conexões com dependências (DB, RabbitMQ, S3).

**Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2026-03-30T10:15:30Z"
}
```

## Arquitetura Clean Architecture

O projeto segue os princípios de **Clean Architecture** com separação clara em camadas:

### 1. Domain (Núcleo)

Contém as regras de negócio fundamentais, sem dependências externas:
- **Entities**: `Diagrama`, `Analise` — objetos com identidade única
- **Value Objects**: `ArquivoDiagrama`, `StatusAnalise` — objetos imutáveis
- **Events**: `DiagramaEnviado` — eventos de domínio
- **Exceptions**: Erros customizados de negócio
- **Ports (Interfaces)**: `DiagramaRepository`, `AnaliseRepository` — contratos abstratos

**Dependências externas permitidas**: Apenas `pydantic` (para validação e modelagem).

### 2. Application (Casos de Uso)

Implementa os cenários de negócio, orquestrando repositórios e serviços:
- **Use Cases**: `SubmitDiagram`, `GetAnalysisStatus`, `HandleStatusUpdate`
- **DTOs**: `AnaliseResponse`, `DiagramaUploadResponse` — dados para entrada/saída
- **Ports (Interfaces)**: `FileStorage`, `EventPublisher` — contratos para infraestrutura

Depende do Domain, mas nunca de implementações concretas de infraestrutura.

### 3. Infrastructure (Detalhes Técnicos)

Implementações concretas de conexões externas:
- **Database**: SQLAlchemy async, migrações com Alembic
- **Messaging**: RabbitMQ (publisher e consumer)
- **Storage**: S3/MinIO (aioboto3)
- **Models**: Mapeamento ORM das tabelas

### 4. Interface (Adapters)

Adapta as camadas internas aos protocolos externos:
- **Controllers**: Rotas FastAPI que delegam para use cases
- **Gateways**: Implementações concretas dos Ports (ex: `SQLAlchemyAnaliseRepository`, `S3FileStorageGateway`)
- **Presenters**: Formatadores de respostas HTTP

### Fluxo de uma Requisição

```
1. POST /api/v1/analises (Controller)
   ↓
2. SubmitDiagram.execute() (Use Case)
   ↓
3. Valida arquivo (Domain logic)
   ↓
4. Upload S3FileStorageGateway.upload_file() (Adapter → Infra)
   ↓
5. Salva Diagrama/Analise via SQLAlchemy (Adapter → Infra)
   ↓
6. Publica evento via RabbitMQEventPublisher (Adapter → Infra)
   ↓
7. Retorna 202 com analise_id
```

### Inversão de Dependência (Ports & Adapters)

Use cases injetam Ports (interfaces abstratas), não Adapters (implementações concretas):

```python
# Correto: Use case depende de Ports, implementações são injetadas
use_case = SubmitDiagram(
    diagrama_repository=SQLAlchemyDiagramaRepository(session),  # Implementação
    analise_repository=SQLAlchemyAnaliseRepository(session),    # Implementação
    file_storage=S3FileStorageGateway(),                       # Implementação
    event_publisher=RabbitMQEventPublisherGateway(),          # Implementação
)
```

Testes unitários usam mocks dos Ports, nunca acessam banco real:

```python
# Mock de Port
class MockDiagramaRepository(DiagramaRepository):
    async def salvar(self, diagrama: Diagrama) -> Diagrama:
        # Implementação fake
        pass

# Teste injeta mock
use_case = SubmitDiagram(
    diagrama_repository=MockDiagramaRepository(),
    # ...
)
```

## Variáveis de Ambiente

Veja `env.example` para a lista completa. As principais:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DATABASE_HOST` | localhost | Host PostgreSQL |
| `DATABASE_PORT` | 5432 | Porta PostgreSQL |
| `DATABASE_USER` | upload_user | Usuário DB |
| `DATABASE_PASSWORD` | upload_pass | Senha DB |
| `DATABASE_NAME` | upload_db | Nome do banco |
| `RABBITMQ_HOST` | localhost | Host RabbitMQ |
| `RABBITMQ_PORT` | 5672 | Porta RabbitMQ |
| `RABBITMQ_EXCHANGE_NAME` | analise.events | Exchange para publicação |
| `RABBITMQ_QUEUE_NAME` | upload-service.status-updates | Fila de consumo |
| `S3_ENDPOINT_URL` | http://localhost:4566 | Endpoint S3/MinIO |
| `S3_BUCKET_NAME` | archlens-diagramas | Nome do bucket |
| `DEBUG` | false | Ativa modo debug |
| `LOG_LEVEL` | INFO | Nível de log (DEBUG, INFO, WARNING, ERROR) |

## Recursos Adicionais

- **Logging**: Utiliza `structlog` com contexto estruturado
- **Resiliência**: Circuit breaker (`pybreaker`), retry com backoff (`tenacity`)
- **Monitoramento**: Integração com New Relic (`newrelic`)
- **Validação**: Pydantic para tipos e validação automática

## Suporte

Para dúvidas ou problemas, consulte a documentação do projeto principal ou entre em contato com a equipe de arquitetura.
