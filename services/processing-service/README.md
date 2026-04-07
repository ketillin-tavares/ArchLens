# Processing Service - ArchLens

Microsserviço responsável por consumir eventos de diagramas enviados via RabbitMQ, processar imagens através de LLM vision (com suporte a pipeline multi-agent), extrair componentes arquiteturais e identificar riscos. Utiliza Clean Architecture com Ports & Adapters, integração com PydanticAI v1.38.0, e observabilidade com New Relic.

## Descrição do Projeto

O **Processing Service** é o núcleo de inteligência do ArchLens. Consome eventos de diagramas de arquitetura enviados pelo Upload Service através do RabbitMQ, normaliza as imagens (PNG, JPEG, PDF), executa análise via LLM vision para identificar componentes arquiteturais e seus riscos, persiste os resultados em PostgreSQL e publica eventos assíncronos para outras partes da plataforma.

O serviço segue **Clean Architecture** com separação rigorosa entre camadas (Domínio, Casos de Uso, Adaptadores e Frameworks), implementando o padrão **Ports & Adapters** para máxima desacoplamento e testabilidade.

## Estrutura de Diretórios

```
src/
├── domain/                           # Camada de Domínio (regras de negócio puras)
│   ├── entities/                     # Entidades de domínio
│   │   ├── processamento.py          # Entidade Processamento (orquestração de análise)
│   │   ├── componente.py             # Entidade Componente (arquitetura identificado)
│   │   ├── risco.py                  # Entidade Risco (problema de arquitetura)
│   │   └── __init__.py
│   ├── repositories/                 # Ports (interfaces abstratas)
│   │   ├── processamento_repository.py  # Port para persistência de processamentos
│   │   └── __init__.py
│   ├── events.py                     # Eventos de domínio (ProcessamentoIniciado, AnaliseConcluida, etc)
│   ├── exceptions.py                 # Exceções de domínio (LLMApiError, ImageProcessingError, etc)
│   ├── schemas.py                    # Schemas de validação de resposta da análise
│   ├── value_objects.py              # Value Objects de domínio
│   ├── prompts/                      # Prompts para LLM (separados por agent)
│   │   ├── analyzer_prompts.py       # Prompts para o analyzer agent
│   │   ├── extractor_prompts.py      # Prompts para o extractor agent
│   │   ├── judge_prompts.py          # Prompts para o judge agent (validação)
│   │   └── __init__.py
│   └── __init__.py
│
├── application/                      # Camada de Casos de Uso
│   ├── use_cases/                   # Casos de uso da aplicação
│   │   ├── process_diagram.py        # Orquestra todo o pipeline de análise
│   │   ├── get_processing_result.py  # Consulta resultado do processamento
│   │   └── __init__.py
│   ├── ports/                       # Ports (interfaces para infraestrutura)
│   │   ├── event_publisher.py       # Port para publicar eventos
│   │   ├── file_storage.py          # Port para armazenamento de arquivos (S3)
│   │   ├── image_processor.py       # Port para processamento de imagens
│   │   ├── llm_client.py            # Port para chamadas ao LLM
│   │   ├── analysis_pipeline.py     # Port para execução do pipeline de análise
│   │   └── __init__.py
│   ├── dtos/                        # Data Transfer Objects (resposta HTTP)
│   │   ├── processamento_response.py # Resposta padronizada
│   │   └── __init__.py
│   ├── validation.py                # Validações de entrada
│   ├── sanity_checks.py             # Verificações de sanidade na resposta do LLM
│   └── __init__.py
│
├── interface/                        # Camada de Interface Adapters
│   ├── controllers/                 # Controllers/Rotas FastAPI
│   │   ├── v1/
│   │   │   ├── processamento_controller.py  # Rotas v1 de processamentos
│   │   │   └── __init__.py
│   │   ├── health_controller.py       # Health check
│   │   └── __init__.py
│   ├── gateways/                    # Adapters (implementações dos Ports)
│   │   ├── processamento_repository_gateway.py   # SQLAlchemy adapter
│   │   ├── event_publisher_gateway.py            # RabbitMQ publisher adapter
│   │   ├── file_storage_gateway.py               # S3 storage adapter
│   │   ├── image_processor_gateway.py            # Imagem processing adapter (FitzImageProcessor)
│   │   ├── llm_client_gateway.py                 # PydanticAI LLM client adapter
│   │   ├── analysis_pipeline_gateway.py          # Pipeline (multi-agent e single-call)
│   │   └── __init__.py
│   ├── presenters/                  # Apresentadores de erro
│   │   ├── error_presenter.py
│   │   ├── health_presenter.py
│   │   └── __init__.py
│   └── __init__.py
│
├── infrastructure/                   # Camada de Frameworks & Drivers
│   ├── database/                    # Acesso ao banco de dados
│   │   ├── session.py               # Factory de sessões SQLAlchemy async
│   │   └── __init__.py
│   ├── models/                      # Modelos SQLAlchemy (mapeamento ORM)
│   │   ├── base.py                  # Base model declarativo
│   │   ├── processamento_model.py   # Modelo para Processamento
│   │   ├── componente_model.py      # Modelo para Componente
│   │   ├── risco_model.py           # Modelo para Risco
│   │   ├── risco_componente_model.py # Modelo de relacionamento N:N
│   │   └── __init__.py
│   ├── messaging/                   # Integração com RabbitMQ
│   │   ├── publisher.py             # Publicador de eventos RabbitMQ
│   │   ├── consumer.py              # Consumidor de eventos DiagramaEnviado
│   │   ├── shared.py                # Instância global do publisher
│   │   └── __init__.py
│   ├── storage/                     # Integração com S3/MinIO
│   │   ├── s3_client.py             # Client aioboto3 para S3
│   │   └── __init__.py
│   ├── llm/                         # Integração com LLM
│   │   ├── llm_client.py            # Client PydanticAI para LiteLLM
│   │   └── __init__.py
│   ├── image/                       # Processamento de imagens
│   │   ├── image_processor.py       # FitzImageProcessor (normaliza PNG/JPEG/PDF)
│   │   └── __init__.py
│   ├── agents/                      # Multi-agent pipeline (PydanticAI)
│   │   ├── analyzer_agent.py        # Agent para análise de arquitetura
│   │   ├── extractor_agent.py       # Agent para extração de componentes/riscos
│   │   ├── judge_agent.py           # Agent para validação de resultados
│   │   ├── multi_agent_pipeline.py  # Orquestrador de múltiplos agents
│   │   ├── single_call_pipeline.py  # Pipeline single-call (modo simples)
│   │   ├── schemas.py               # Schemas dos agents
│   │   └── __init__.py
│   ├── observability/               # Logging, métricas, tracing
│   │   ├── logging.py               # Configuração loguru
│   │   ├── metrics.py               # Recorder de métricas
│   │   ├── tracing.py               # New Relic distributed tracing
│   │   └── __init__.py
│   ├── alembic/                     # Migrações de banco de dados
│   │   ├── env.py
│   │   └── versions/
│   └── __init__.py
│
├── environment.py                    # Configurações (Pydantic Settings)
├── main.py                          # Aplicação FastAPI principal
└── __init__.py

tests/
├── test_domain/                     # Testes de entidades e value objects
│   ├── test_entities.py
│   ├── test_events.py
│   ├── test_exceptions.py
│   ├── test_schemas.py
│   └── __init__.py
├── test_application/                # Testes de casos de uso
│   ├── test_use_cases.py
│   ├── test_validation.py
│   ├── test_sanity_checks.py
│   └── __init__.py
├── test_interface/                  # Testes de controllers e gateways
│   ├── test_controllers.py
│   ├── test_gateways.py
│   ├── test_health_controller.py
│   └── __init__.py
├── test_infrastructure/             # Testes de infraestrutura
│   ├── test_s3_client.py
│   ├── test_image_processor.py
│   ├── test_llm_client.py
│   ├── test_agents.py
│   ├── test_messaging.py
│   ├── test_observability.py
│   └── __init__.py
├── test_main.py                     # Testes de integração
├── conftest.py                      # Fixtures de testes
└── __init__.py
```

## Arquitetura e Camadas

A aplicação segue **Clean Architecture** com inversão de dependências via **Ports & Adapters**:

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do serviço (ou use `env.example` como base):

```bash
# Banco de Dados PostgreSQL
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_USER=processing_user
DATABASE_PASSWORD=processing_pass
DATABASE_NAME=processing_db

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=archlens
RABBITMQ_PASSWORD=archlens_dev
RABBITMQ_EXCHANGE_NAME=analise.events
RABBITMQ_QUEUE_NAME=processing-service.pipeline

# S3/MinIO
S3_ENDPOINT_URL=http://localstack:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_BUCKET_NAME=archlens-diagramas
AWS_REGION=us-east-1

# LLM (LiteLLM Proxy)
LLM_BASE_URL=http://litellm:4000
LLM_API_KEY=sk-litellm
LLM_MODEL_NAME=archlens-vision
LLM_ANALYZER_MODEL_NAME=archlens-analyzer
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096

# Multi-Agent Pipeline
ENABLE_MULTIAGENT=true
ENABLE_JUDGE=false

# Aplicação
SERVICE_NAME=processing-service
DEBUG=false
LOG_LEVEL=INFO

# New Relic (Observabilidade)
NEW_RELIC_USER_KEY=<sua_chave>
NEW_RELIC_LICENSE_KEY=<sua_chave>
NEW_RELIC_ACCOUNT_ID=<seu_account_id>
NRIA_DISPLAY_NAME=processing-service
NRIA_LICENSE_KEY=<sua_chave>
```

## Como Rodar Localmente

### Pré-requisitos

- **Python** 3.13+
- **UV** (gerenciador de pacotes)
- **Docker & Docker Compose** (para infraestrutura local)

### Instalação de Dependências

```bash
cd services/processing-service

# Instalar UV (se não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependências
uv sync
```

### Configuração do Ambiente

```bash
# Copiar variáveis de exemplo
cp env.example .env

# Caso esteja desenvolvendo, ainda assim é necessário um banco local
# Ver seção "Rodando a Infraestrutura"
```

### Rodando a Infraestrutura (Docker Compose)

Na raiz do projeto ArchLens, execute:

```bash
# Subir PostgreSQL, RabbitMQ, S3/MinIO, Vault, LiteLLM, Kong, etc.
docker compose up -d

# Verificar saúde
docker compose ps
```

Aguarde alguns segundos para os serviços estabilizarem.

### Rodando o Serviço

#### Via Bare Metal

```bash
# Aplicar migrações
uv run alembic upgrade head

# Iniciar servidor (porta 8001)
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

A aplicação estará disponível em `http://localhost:8001`.

#### Via Docker

```bash
# Build da imagem (multistage)
docker build -t archlens-processing-service:latest .

# Rodar container (usa variáveis do .env)
docker run --env-file .env -p 8001:8001 archlens-processing-service:latest
```

### Verificar Saúde

```bash
curl http://localhost:8001/health
```

## Endpoints da API

### GET /v1/processamentos/{analise_id}

Consulta o resultado do processamento para uma análise.

**Parâmetros:**
- `analise_id` (path, UUID): Identificador único da análise.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "analise_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "concluido",
  "tentativas": 1,
  "iniciado_em": "2026-04-02T10:15:30Z",
  "concluido_em": "2026-04-02T10:15:45Z",
  "erro_detalhe": null,
  "componentes": [
    {
      "id": "comp_1",
      "nome": "API Gateway",
      "descricao": "Ponto de entrada da aplicação",
      "tipo": "gateway"
    }
  ],
  "riscos": [
    {
      "id": "risk_1",
      "titulo": "Single Point of Failure",
      "descricao": "API Gateway sem redundância",
      "severidade": "critica",
      "componentes_afetados": ["comp_1"]
    }
  ]
}
```

**Códigos de erro:**
- `404 Not Found`: Processamento não encontrado para a análise

### GET /health

Health check que valida a saúde do serviço e suas dependências (DB, RabbitMQ, S3, LLM).

**Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2026-04-02T10:15:30Z"
}
```

## Testes e QA

Os testes seguem o padrão AAA (Arrange, Act, Assert) e usam mocks para Ports (interfaces), nunca acessando implementações concretas como banco de dados real.

### Executar todos os testes

```bash
uv run pytest
```

### Testes com cobertura detalhada

```bash
uv run pytest --cov=src --cov-report=html --cov-report=term-missing
```

Gera relatório HTML em `htmlcov/index.html`.

### Executar apenas um arquivo de testes

```bash
uv run pytest tests/test_application/test_use_cases.py -v
```

### Executar apenas um teste específico

```bash
uv run pytest tests/test_application/test_use_cases.py::test_process_diagram -v
```

### Testes em modo watch (reexecuta ao alterar arquivos)

```bash
uv run pytest --lf -v
```

### Linter (Ruff) - Verificação de código

Verificar problemas de estilo e imports:

```bash
uv run ruff check src tests
```

Corrigir automaticamente problemas encontrados:

```bash
uv run ruff check src tests --fix
```

Formatar código (linha com 120 caracteres máximo):

```bash
uv run ruff format src tests
```

### Type Checking (Mypy via `ty`)

Verificar tipos estáticos:

```bash
uv run ty check src/
```

### Executar todo o pipeline de qualidade

Combina formatação, linter, type checking e testes com cobertura:

```bash
make quality
```

Ou manualmente:

```bash
uv run ruff format src tests
uv run ruff check --fix src tests
uv run ty check src/
uv run pytest --cov=src --cov-report=term-missing
```

## Recursos Adicionais

- **LLM Vision**: PydanticAI v1.38.0 para chamadas estruturadas ao LLM
- **Multi-Agent Pipeline**: Orquestração de múltiplos agents (Analyzer, Extractor, Judge)
- **Processamento de Imagens**: PyMuPDF (FitzImageProcessor) para normalizar diversos formatos
- **Logging**: Utiliza `loguru` com contexto estruturado
- **Resiliência**: Circuit breaker (`pybreaker`), retry com backoff (`tenacity`)
- **Monitoramento**: Integração com New Relic (`newrelic`)
- **Validação**: Pydantic para tipos e validação automática
- **Async/Await**: Operações totalmente assíncronas

## Padrões de Tratamento de Erros

O serviço classifica exceções do LLM em dois grupos para determinar se deve fazer retry:

**Não Retriáveis (falha permanente):**
- `LLMContentFilterError`: Resposta bloqueada por filtro de conteúdo
- `LLMContextWindowError`: Contexto excedeu o limite do modelo
- `AnaliseInsanaError`: Falha nos sanity checks
- `ImageProcessingError`: Falha ao normalizar imagem

**Retriáveis (tenta novamente):**
- `LLMApiError`: Erro genérico de API (timeout, rate limit)
- `StorageDownloadError`: Falha ao baixar arquivo do S3

A camada de Interface Adapters traduz exceções de domínio para códigos HTTP apropriados.

## Suporte

Para dúvidas ou problemas, consulte a documentação do projeto principal ou entre em contato com a equipe de arquitetura.
