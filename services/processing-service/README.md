# Processing Service

Serviço responsável por consumir eventos de diagramas enviados via RabbitMQ, normalizar imagens, enviar para análise de arquitetura via LLM e persistir resultados em PostgreSQL, emitindo eventos de conclusão ou falha.

## Estrutura do Projeto

```
services/processing-service/
├── src/                                  # Código-fonte da aplicação
│   ├── domain/                          # Camada de Domínio (regras de negócio)
│   │   ├── entities/                    # Entidades: Processamento, Componente, Risco
│   │   ├── events.py                    # Eventos de domínio: DiagramaEnviado, AnaliseConcluida, AnaliseFalhou
│   │   ├── exceptions.py                # Exceções customizadas de domínio
│   │   ├── schemas.py                   # Esquemas de dados de domínio
│   │   ├── value_objects.py             # Objetos de valor do domínio
│   │   └── repositories/                # Interfaces (Ports) de repositórios
│   │       └── processamento_repository.py  # Contrato de persistência
│   │
│   ├── application/                     # Camada de Aplicação (casos de uso)
│   │   ├── use_cases/                   # Casos de uso: ProcessDiagram, GetProcessingResult
│   │   ├── dtos/                        # Data Transfer Objects
│   │   │   └── processamento_response.py    # Resposta padronizada de processamento
│   │   ├── ports/                       # Interfaces (Ports)
│   │   │   ├── event_publisher.py       # Contrato para publicação de eventos
│   │   │   ├── file_storage.py          # Contrato para acesso ao S3
│   │   │   ├── image_processor.py       # Contrato para normalização de imagens
│   │   │   └── llm_client.py            # Contrato para comunicação com LLM
│   │   ├── sanity_checks.py             # Validações pós-análise de integridade
│   │   └── validation.py                # Validações de negócio
│   │
│   ├── infrastructure/                  # Camada de Infraestrutura (detalhes técnicos)
│   │   ├── database/                    # Conexão e sessões SQLAlchemy async
│   │   │   ├── session.py               # Configuração de conexão async
│   │   │   └── __init__.py
│   │   ├── models/                      # Modelos SQLAlchemy (mapeamento de tabelas)
│   │   │   ├── base.py                  # Classe base para modelos
│   │   │   ├── processamento_model.py   # Modelo ORM para Processamento
│   │   │   ├── componente_model.py      # Modelo ORM para Componente
│   │   │   ├── risco_model.py           # Modelo ORM para Risco
│   │   │   ├── risco_componente_model.py # Modelo ORM para Risco-Componente
│   │   │   └── __init__.py
│   │   ├── messaging/                   # RabbitMQ (pub/sub)
│   │   │   ├── consumer.py              # Consumidor de eventos DiagramaEnviado
│   │   │   ├── publisher.py             # Publicador de eventos AnaliseConcluida/AnaliseFalhou
│   │   │   ├── shared.py                # Instância global do publisher
│   │   │   └── __init__.py
│   │   ├── storage/                     # S3 / Object Storage
│   │   │   ├── s3_client.py             # Cliente S3 para download de diagramas
│   │   │   └── __init__.py
│   │   ├── image/                       # Processamento de imagens
│   │   │   ├── image_processor.py       # Normalização e redimensionamento
│   │   │   └── __init__.py
│   │   ├── llm/                         # Integração com LLM via LiteLLM Proxy
│   │   │   ├── llm_client.py            # Cliente HTTP para envio de imagens e análise
│   │   │   └── __init__.py
│   │   ├── observability/               # Logging e métricas
│   │   │   ├── logging.py               # Configuração de logging estruturado
│   │   │   ├── metrics.py               # Métricas da aplicação
│   │   │   └── __init__.py
│   │   ├── alembic/                     # Migrações de banco de dados
│   │   │   ├── versions/                # Scripts de migração
│   │   │   └── env.py                   # Configuração do Alembic
│   │   └── __init__.py
│   │
│   ├── interface/                       # Camada de Interface Adapters
│   │   ├── controllers/                 # Rotas HTTP (FastAPI)
│   │   │   ├── v1/                      # Versão 1 da API
│   │   │   │   ├── processamento_controller.py # Endpoints: GET /processamentos/{diagrama_id}
│   │   │   │   └── __init__.py
│   │   │   ├── health_controller.py     # Health check
│   │   │   └── __init__.py
│   │   ├── gateways/                    # Implementações concretas (Adapters)
│   │   │   ├── processamento_repository_gateway.py   # SQLAlchemy adapter para Processamento
│   │   │   ├── event_publisher_gateway.py            # RabbitMQ adapter para pub/sub
│   │   │   ├── file_storage_gateway.py               # S3 adapter para download de diagramas
│   │   │   ├── image_processor_gateway.py            # Adapter para normalização de imagens
│   │   │   ├── llm_client_gateway.py                 # LiteLLM Proxy adapter
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
│   ├── test_domain/                     # Testes de entidades e schemas
│   ├── test_application/                # Testes de casos de uso (mocks de Ports)
│   ├── test_interface/                  # Testes de controllers (integração HTTP)
│   └── __init__.py
│
├── pyproject.toml                       # Configuração do projeto (uv, pytest, ruff)
├── alembic.ini                          # Configuração das migrações
├── newrelic.ini                         # Configuração do New Relic
├── Dockerfile                           # Build multistage (builder + runtime)
├── docker-compose.yml                   # Orquestração local (app, DB, RabbitMQ, S3, LLM)
├── docker/                              # Docker auxiliares
│   └── postgres/                        # Dockerfile customizado do PostgreSQL com New Relic
├── env.example                          # Variáveis de ambiente (template)
└── README.md                            # Este arquivo
```

## Pré-requisitos

- Python 3.13+
- Docker e Docker Compose
- uv (gerenciador de dependências)

## Configuração Local

### 1. Navegar até o serviço

```bash
cd services/processing-service
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

Certifique-se de que PostgreSQL, RabbitMQ, LocalStack (S3) e LiteLLM Proxy estão rodando:

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

A aplicação estará disponível em `http://localhost:8001`.

#### Opção B: Docker Compose

```bash
docker-compose up -d
```

Isso inicia:
- **processing-service**: Porta 8001
- **PostgreSQL**: Porta 5432 (volume persistente)
- **RabbitMQ**: Porta 5672 (management UI na porta 15672)
- **LocalStack**: Porta 4566 (S3 emulation)
- **New Relic Infrastructure**: Monitoramento

Para visualizar logs:

```bash
docker-compose logs -f processing-service
```

Para parar todos os serviços:

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
uv run mypy src tests
```

## Endpoints da API

### GET /v1/processamentos/{analise_id}

Recupera resultado de processamento/análise de um diagrama específico.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "diagrama_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "concluida",
  "conteudo_analise": {
    "resumo": "Análise arquitetural do diagrama...",
    "componentes": [
      {
        "id": "comp-001",
        "nome": "API Gateway",
        "tipo": "gateway",
        "riscos": ["single-point-of-failure"]
      }
    ],
    "riscos": [
      {
        "id": "risco-001",
        "nome": "Single Point of Failure",
        "severidade": "alta",
        "componentes_afetados": ["comp-001"]
      }
    ]
  },
  "criado_em": "2026-04-02T10:15:30Z",
  "atualizado_em": "2026-04-02T10:16:00Z"
}
```

**Erros:**
- `404 Not Found`: Processamento não encontrado para o diagrama especificado
- `400 Bad Request`: Processamento falhou ou em estado inválido
- `500 Internal Server Error`: Erro ao recuperar o processamento

### GET /health

Health check que valida conexões com dependências (DB, RabbitMQ, S3, LLM).

**Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2026-04-02T10:15:30Z"
}
```

## Fluxo de Processamento

```
1. RabbitMQ Consumer recebe DiagramaEnviado
   ↓
2. ProcessDiagram.execute() (Use Case)
   ↓
3. Download imagem de diagrama via S3 (Adapter → Infra)
   ↓
4. Normalização de imagem (image processor)
   ↓
5. Envio para LLM via LiteLLM Proxy (Adapter → Infra)
   ↓
6. Validação de resposta LLM (Domain logic)
   ↓
7. Aplicação de sanity checks (validações de integridade)
   ↓
8. Persiste resultado via ProcessamentoRepository (Adapter → Infra)
   ↓
9. Publica AnaliseConcluida ou AnaliseFalhou (Adapter → Infra)
```

## Arquitetura Clean Architecture

O projeto segue os princípios de **Clean Architecture** com separação clara em camadas:

### 1. Domain (Núcleo)

Contém as regras de negócio fundamentais, sem dependências externas:
- **Entities**: `Processamento`, `Componente`, `Risco` — objetos com identidade única
- **Events**: `DiagramaEnviado`, `AnaliseConcluida`, `AnaliseFalhou` — eventos de domínio
- **Exceptions**: Erros customizados de negócio
- **Ports (Interfaces)**: `ProcessamentoRepository`, `EventPublisher`, `FileStorage`, `ImageProcessor`, `LLMClient` — contratos abstratos

**Dependências externas permitidas**: Apenas `pydantic` (para validação e modelagem).

### 2. Application (Casos de Uso)

Implementa os cenários de negócio:
- **Use Cases**: `ProcessDiagram` (consome evento, processa imagem, chama LLM, persiste), `GetProcessingResult` (recupera resultado)
- **DTOs**: `ProcessamentoResponse` — dados para saída
- **Ports (Interfaces)**: `EventPublisher`, `FileStorage`, `ImageProcessor`, `LLMClient` — contratos para dependências externas
- **Sanity Checks**: Validações pós-análise de integridade dos resultados LLM

Depende do Domain, mas nunca de implementações concretas de infraestrutura.

### 3. Infrastructure (Detalhes Técnicos)

Implementações concretas de conexões externas:
- **Database**: SQLAlchemy async, migrações com Alembic
- **Messaging**: RabbitMQ (consumidor de `DiagramaEnviado`, publicador de `AnaliseConcluida`/`AnaliseFalhou`)
- **Storage**: Cliente S3 para download de diagramas
- **Image Processing**: Normalização e redimensionamento de imagens
- **LLM**: Cliente HTTP para LiteLLM Proxy
- **Models**: Mapeamento ORM das tabelas

### 4. Interface (Adapters)

Adapta as camadas internas aos protocolos externos:
- **Controllers**: Rotas FastAPI que delegam para use cases
- **Gateways**: Implementações concretas dos Ports (ex: `SQLAlchemyProcessamentoRepository`, `RabbitMQEventPublisherGateway`, `S3FileStorageGateway`, etc.)
- **Presenters**: Formatadores de respostas HTTP

### Inversão de Dependência (Ports & Adapters)

Use cases injetam Ports (interfaces abstratas), não Adapters (implementações concretas):

```python
# Correto: Use case depende de Ports, implementações são injetadas
use_case = ProcessDiagram(
    processamento_repository=SQLAlchemyProcessamentoRepository(session),  # Implementação
    event_publisher=RabbitMQEventPublisherGateway(),                      # Implementação
    file_storage=S3FileStorageGateway(s3_client),                         # Implementação
    image_processor=ImageProcessorGateway(),                              # Implementação
    llm_client=LiteLLMProxyGateway(base_url, api_key),                   # Implementação
)
```

Testes unitários usam mocks dos Ports, nunca acessam banco real:

```python
# Mock de Port
class MockProcessamentoRepository(ProcessamentoRepository):
    async def salvar(self, processamento: Processamento) -> Processamento:
        # Implementação fake
        pass

# Teste injeta mock
use_case = ProcessDiagram(
    processamento_repository=MockProcessamentoRepository(),
    # ...
)
```

## Variáveis de Ambiente

Veja `env.example` para a lista completa. As principais:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DATABASE_HOST` | localhost | Host PostgreSQL |
| `DATABASE_PORT` | 5432 | Porta PostgreSQL |
| `DATABASE_USER` | processing_user | Usuário DB |
| `DATABASE_PASSWORD` | processing_pass | Senha DB |
| `DATABASE_NAME` | processing_db | Nome do banco |
| `RABBITMQ_HOST` | localhost | Host RabbitMQ |
| `RABBITMQ_PORT` | 5672 | Porta RabbitMQ |
| `RABBITMQ_EXCHANGE_NAME` | analise.events | Exchange para publicação/consumo |
| `RABBITMQ_QUEUE_NAME` | processing-service.pipeline | Fila de consumo de eventos |
| `S3_ENDPOINT_URL` | http://localhost:4566 | Endpoint S3 (LocalStack ou AWS) |
| `S3_BUCKET_NAME` | archlens-diagramas | Bucket S3 para diagramas |
| `LLM_BASE_URL` | http://localhost:4000 | Base URL do LiteLLM Proxy |
| `LLM_API_KEY` | sk-litellm | Chave de API do LLM |
| `LLM_MODEL_NAME` | archlens-vision | Nome do modelo de visão do LLM |
| `LLM_TEMPERATURE` | 0.1 | Temperatura do modelo (consistência) |
| `LLM_MAX_TOKENS` | 4096 | Máximo de tokens na resposta |
| `DEBUG` | false | Ativa modo debug |
| `LOG_LEVEL` | INFO | Nível de log (DEBUG, INFO, WARNING, ERROR) |

## Recursos Adicionais

- **Logging**: Utiliza `loguru` com contexto estruturado
- **Monitoramento**: Integração com New Relic (`newrelic`)
- **Validação**: Pydantic para tipos e validação automática
- **Async/Await**: Operações totalmente assíncronas com asyncpg e aio-pika
- **Processamento de Imagens**: Pillow para normalização
- **Integração LLM**: LiteLLM Proxy para flexibilidade de modelos

## Suporte

Para dúvidas ou problemas, consulte a documentação do projeto principal ou entre em contato com a equipe de arquitetura.
