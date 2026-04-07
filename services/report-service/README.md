# Report Service

Microserviço responsável pela geração, armazenamento e entrega de relatórios arquiteturais. Consome eventos de análise concluída via RabbitMQ, gera relatórios estruturados em Markdown (via LiteLLM) e JSON, persiste em PostgreSQL, armazena em S3 e disponibiliza através de uma API REST. Implementa Clean Architecture com Ports & Adapters, observabilidade com Loguru e New Relic.

## Estrutura do Projeto

```
services/report-service/
├── src/                                  # Código-fonte da aplicação
│   ├── domain/                          # Camada de Domínio (regras de negócio)
│   │   ├── entities/
│   │   │   └── relatorio.py             # Entidade Relatorio com Pydantic
│   │   ├── events.py                    # Eventos de domínio: AnaliseConcluida, RelatorioGerado
│   │   ├── exceptions.py                # Exceções customizadas de domínio
│   │   └── repositories/
│   │       └── relatorio_repository.py  # Port (interface abstrata) de persistência
│   │
│   ├── application/                     # Camada de Aplicação (casos de uso)
│   │   ├── use_cases/
│   │   │   ├── generate_report.py       # Caso de uso: GenerateReport
│   │   │   └── get_report.py            # Caso de uso: GetReport
│   │   ├── dtos/
│   │   │   └── relatorio_response.py    # Data Transfer Object de saída
│   │   └── ports/
│   │       ├── event_publisher.py       # Port: contrato de publicação de eventos
│   │       ├── file_storage.py          # Port: contrato de persistência em S3
│   │       └── markdown_report_writer.py # Port: contrato de geração de Markdown
│   │
│   ├── infrastructure/                  # Camada de Infraestrutura (detalhes técnicos)
│   │   ├── database/
│   │   │   ├── session.py               # Configuração de conexão async (asyncpg)
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   ├── base.py                  # Classe base para modelos SQLAlchemy
│   │   │   ├── relatorio_model.py       # Modelo ORM mapeado para tabela
│   │   │   └── __init__.py
│   │   ├── messaging/
│   │   │   ├── consumer.py              # RabbitMQ Consumer de AnaliseConcluida
│   │   │   ├── publisher.py             # RabbitMQ Publisher de RelatorioGerado
│   │   │   ├── shared.py                # Instância global do publisher
│   │   │   └── __init__.py
│   │   ├── storage/
│   │   │   ├── s3_client.py             # Cliente aioboto3 para S3/LocalStack
│   │   │   └── __init__.py
│   │   ├── observability/
│   │   │   ├── logging.py               # Configuração de Loguru com sink para stdlib
│   │   │   ├── metrics.py               # Recorder de métricas customizadas
│   │   │   └── __init__.py
│   │   ├── alembic/
│   │   │   ├── versions/                # Scripts de migração
│   │   │   └── env.py                   # Configuração Alembic
│   │   └── __init__.py
│   │
│   ├── interface/                       # Camada de Interface Adapters
│   │   ├── controllers/
│   │   │   ├── v1/
│   │   │   │   ├── relatorio_controller.py  # Rotas FastAPI v1
│   │   │   │   └── __init__.py
│   │   │   ├── health_controller.py     # Health check
│   │   │   └── __init__.py
│   │   ├── gateways/
│   │   │   ├── relatorio_repository_gateway.py   # Adapter: SQLAlchemy -> Port
│   │   │   ├── event_publisher_gateway.py        # Adapter: RabbitMQ -> Port
│   │   │   ├── file_storage_gateway.py           # Adapter: aioboto3 S3 -> Port
│   │   │   ├── markdown_report_writer_gateway.py # Adapter: PydanticAI LiteLLM -> Port
│   │   │   └── __init__.py
│   │   ├── presenters/
│   │   │   ├── health_presenter.py      # Formatador de resposta health
│   │   │   ├── error_presenter.py       # Formatador de erros HTTP
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── environment.py                   # Settings com Pydantic (banco, RabbitMQ, S3, LLM)
│   ├── main.py                          # FastAPI app, lifespan, exception handlers
│   └── __init__.py
│
├── tests/                               # Testes automatizados (108 testes, 91% cobertura)
│   ├── test_domain/                     # Testes de entidades e exceções
│   ├── test_application/                # Testes de use cases com mocks de Ports
│   ├── test_interface/                  # Testes de controllers (integração HTTP)
│   ├── test_infrastructure/             # Testes de observability
│   ├── conftest.py                      # Fixtures compartilhadas
│   └── __init__.py
│
├── Makefile                             # Atalhos de comandos (make quality, test-cov, etc)
├── pyproject.toml                       # Configuração uv, pytest, ruff
├── alembic.ini                          # Configuração Alembic
├── newrelic.ini                         # Configuração New Relic
├── Dockerfile                           # Multistage build (builder + runtime)
├── docker-compose.yml                   # Orquestração local (app, DB, RabbitMQ, migrations)
├── docker/
│   └── postgres/
│       └── Dockerfile                   # PostgreSQL com New Relic Infrastructure
├── env.example                          # Template de variáveis de ambiente
└── README.md                            # Este arquivo
```

## Pré-requisitos

- **Python**: 3.13 ou superior
- **uv**: Gerenciador de dependências (https://docs.astral.sh/uv/getting-started/)
- **Docker e Docker Compose**: Para execução containerizada (opcional para desenvolvimento local)
- **PostgreSQL**: 15+ (necessário se rodar sem Docker)
- **RabbitMQ**: 3.x (necessário se rodar sem Docker)

## Configuração e Execução Local

### 1. Navegar até o serviço

```bash
cd services/report-service
```

### 2. Preparar variáveis de ambiente

```bash
cp env.example .env
```

Edite `.env` conforme necessário. As variáveis padrão estão otimizadas para Docker Compose (hostnomes de container). Para desenvolvimento bare metal, substitua hostnames pelos valores localhost.

### 3. Instalar dependências

```bash
uv sync
```

Isso cria um ambiente virtual e instala todas as dependências (produção e desenvolvimento).

### 4. Executar a aplicação

#### Opção A: Docker Compose (Recomendado)

```bash
docker-compose up -d
```

Inicia automaticamente:
- **report-service**: Porta 8002 (FastAPI)
- **PostgreSQL**: Porta 5432 (volume persistente)
- **RabbitMQ**: Portas 5672 (AMQP) e 15672 (Management)
- **Migrations**: Alembic upgrade head (automático)
- **New Relic Infrastructure**: Agente de monitoramento (requer `NRIA_LICENSE_KEY`)

**Visualizar logs da aplicação:**

```bash
docker-compose logs -f report-service
```

**Acessar o PostgreSQL via psql:**

```bash
docker-compose exec postgres psql -U report_user -d report_db
```

**Acessar RabbitMQ Management:**

Abra `http://localhost:15672` (credenciais: veja `env.example`)

**Parar todos os serviços:**

```bash
docker-compose down
```

**Remover volumes persistentes (limpa banco de dados):**

```bash
docker-compose down -v
```

#### Opção B: Bare Metal (Desenvolvimento Local)

Certifique-se de que PostgreSQL (porta 5432) e RabbitMQ (porta 5672) estão rodando localmente.

Aplicar migrações:

```bash
uv run alembic upgrade head
```

Iniciar a aplicação com reload automático:

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

A aplicação estará disponível em `http://localhost:8002`.

**Health check:**

```bash
curl http://localhost:8002/health
```

## Testes e Qualidade de Código

Os testes seguem o padrão **AAA** (Arrange, Act, Assert) e usam mocks para Ports (interfaces abstratas), nunca acessando implementações concretas como banco de dados real.

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
uv run pytest tests/test_application/ -v
```

### Executar apenas um teste específico

```bash
uv run pytest tests/test_application/test_use_cases.py::test_generate_report -v
```

### Linter e Formatação (Ruff)

**Verificar estilo e imports:**

```bash
uv run ruff check src tests
```

**Corrigir automaticamente:**

```bash
uv run ruff check --fix src tests
```

**Formatar código (máximo 120 caracteres por linha):**

```bash
uv run ruff format src tests
```

### Type Checking (mypy via `ty`)

```bash
uv run ty check src/
```

### Pipeline de Qualidade Completo

Atalho que executa formatação, linting, type checking e testes com cobertura:

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

**Atalhos disponíveis no Makefile:**

```bash
make format       # Formata código
make lint         # Verifica e corrige imports/estilo
make typecheck    # Type checking
make test-cov     # Testes com cobertura
make quality      # Pipeline completo
```

## Endpoints da API

### GET /v1/relatorios/{analise_id}

Recupera um relatório já gerado para uma análise específica pelo UUID da análise.

**Parâmetros:**
- `analise_id` (path, UUID): Identificador único da análise.

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "analise_id": "660e8400-e29b-41d4-a716-446655440001",
  "titulo": "Relatório de Análise Arquitetural",
  "resumo": "Foram identificados 5 componentes arquiteturais e 3 riscos.",
  "conteudo": {
    "componentes": [
      {
        "id": "comp_1",
        "nome": "API Gateway"
      },
      {
        "id": "comp_2",
        "nome": "Auth Service"
      }
    ],
    "riscos": [
      {
        "id": "risk_1",
        "severidade": "critica",
        "descricao": "Critical security issue"
      }
    ],
    "estatisticas": {
      "total_componentes": 5,
      "total_riscos": 3,
      "riscos_por_severidade": {
        "critica": 1,
        "alta": 1,
        "media": 1,
        "baixa": 0
      }
    }
  },
  "s3_key": "relatorios/660e8400-e29b-41d4-a716-446655440001.md",
  "criado_em": "2026-03-30T10:15:30Z"
}
```

**Códigos de erro:**

- `404 Not Found`: Relatório não encontrado (ainda não foi gerado ou análise inválida)
- `500 Internal Server Error`: Erro interno ao recuperar o relatório

**Exemplo:**

```bash
curl -X GET "http://localhost:8002/v1/relatorios/660e8400-e29b-41d4-a716-446655440001"
```

### GET /health

Health check que valida a saúde do serviço e suas dependências.

**Response (200 OK):**

```json
{
  "status": "ok",
  "timestamp": "2026-03-30T10:15:30Z"
}
```

**Exemplo:**

```bash
curl http://localhost:8002/health
```

## Arquitetura Clean Architecture

O projeto segue rigorosamente os princípios de **Clean Architecture** com separação clara de responsabilidades e inversão de dependência obrigatória via Ports & Adapters.

## Variáveis de Ambiente

O arquivo `env.example` contém todas as variáveis de configuração. Copie para `.env` antes de executar:

```bash
cp env.example .env
```

As configurações são carregadas via **Pydantic Settings** em `environment.py` com validação automática.

### Banco de Dados (PostgreSQL)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DATABASE_HOST` | postgres | Host do PostgreSQL (postgres em Docker Compose) |
| `DATABASE_PORT` | 5432 | Porta do PostgreSQL |
| `DATABASE_USER` | report_user | Usuário do banco |
| `DATABASE_PASSWORD` | report_pass | Senha do banco |
| `DATABASE_NAME` | report_db | Nome do banco de dados |

**Nota**: Em Docker Compose, use `postgres` como host. Para bare metal, use `localhost`.

### RabbitMQ (Message Broker)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `RABBITMQ_HOST` | rabbitmq | Host do RabbitMQ (rabbitmq em Docker Compose) |
| `RABBITMQ_PORT` | 5672 | Porta AMQP |
| `RABBITMQ_USER` | archlens | Usuário RabbitMQ |
| `RABBITMQ_PASSWORD` | archlens_dev | Senha RabbitMQ |
| `RABBITMQ_EXCHANGE_NAME` | analise.events | Exchange para pub/sub de eventos |
| `RABBITMQ_QUEUE_NAME` | report-service.reports | Fila dedicada para consumir `AnaliseConcluida` |

### S3/LocalStack (Object Storage)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `S3_ENDPOINT_URL` | http://localstack:4566 | URL do S3/LocalStack (localstack em Docker) |
| `AWS_ACCESS_KEY_ID` | test | Chave de acesso AWS (dummy para LocalStack) |
| `AWS_SECRET_ACCESS_KEY` | test | Chave secreta AWS (dummy para LocalStack) |
| `S3_BUCKET_NAME` | archlens-diagramas | Bucket para armazenar relatórios Markdown |
| `AWS_REGION` | us-east-1 | Região AWS |

### LLM (Geração de Markdown via LiteLLM)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LLM_BASE_URL` | http://litellm:4000 | URL do proxy LiteLLM (litellm em Docker) |
| `LLM_API_KEY` | sk-litellm-dev | Chave API do LiteLLM |
| `LLM_MODEL_NAME` | archlens-analyzer | Modelo LLM configurado no LiteLLM |

### Aplicação

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SERVICE_NAME` | report-service | Nome do serviço (para logs estruturados) |
| `DEBUG` | false | Ativa modo debug (False em produção) |
| `LOG_LEVEL` | INFO | Nível de logging (DEBUG, INFO, WARNING, ERROR) |

### New Relic (Observabilidade)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `NEW_RELIC_USER_KEY` | abc | Chave de usuário New Relic (deixe em branco se não usar) |
| `NEW_RELIC_LICENSE_KEY` | abc | Licença New Relic (deixe em branco se não usar) |
| `NEW_RELIC_ACCOUNT_ID` | 123 | ID da conta New Relic |
| `NRIA_DISPLAY_NAME` | report-service | Nome exibido no New Relic Infrastructure |
| `NRIA_LICENSE_KEY` | abc | Licença do agente New Relic Infrastructure |

**Nota sobre New Relic**: O serviço funciona normalmente sem essas credenciais. Se estiver vazio, os agentes simplesmente não enviarão dados.

### Guia de Configuração por Ambiente

#### Docker Compose (Recomendado)

Use os valores de `env.example` conforme fornecidos. Os hostnames referem-se aos nomes dos containers na rede interna.

#### Bare Metal (Desenvolvimento Local)

Edite `.env` e substitua os hostnames por `localhost`:

```bash
DATABASE_HOST=localhost
RABBITMQ_HOST=localhost
S3_ENDPOINT_URL=http://localhost:4566
LLM_BASE_URL=http://localhost:4000
```

Certifique-se de que os serviços (PostgreSQL, RabbitMQ, LocalStack, LiteLLM) estão rodando localmente nas portas corretas.

## Tecnologias e Dependências

### Principais Bibliotecas

| Biblioteca | Versão | Propósito |
|------------|--------|----------|
| **FastAPI** | >=0.115.0 | Framework web assíncrono |
| **Uvicorn** | >=0.34.0 | Servidor ASGI |
| **Pydantic** | >=2.10.0 | Validação de dados e settings |
| **SQLAlchemy** | >=2.0.36 | ORM assíncrono |
| **asyncpg** | >=0.30.0 | Driver PostgreSQL async |
| **Alembic** | >=1.14.0 | Migrações de banco de dados |
| **aio-pika** | >=9.5.0 | Cliente RabbitMQ assíncrono |
| **aioboto3** | >=15.5.0 | Cliente AWS S3 assíncrono |
| **PydanticAI** | >=1.38.0 | Framework para agentes com LLMs |
| **Loguru** | >=0.7.0 | Logging estruturado |
| **newrelic** | >=10.0.0 | Observabilidade com New Relic |

### Dependências de Desenvolvimento

- **pytest** >=8.3.0 — Framework de testes
- **pytest-asyncio** >=0.24.0 — Plugin para testes async
- **pytest-cov** — Cobertura de código
- **ruff** >=0.8.0 — Linter e formatador ultra-rápido
- **ty** >=0.0.26 — Type checker (mypy)
- **pre-commit** >=4.5.1 — Git hooks automatizados

## Docker

### Multistage Build

O `Dockerfile` utiliza arquitetura de multistage build:

1. **Stage `builder`**: Compila dependências Python em ambiente isolado
2. **Stage `runtime`**: Copia apenas os artefatos necessários para imagem final

Isso reduz drasticamente o tamanho da imagem final.

### Build e Execução

**Build da imagem:**

```bash
docker build -t report-service:latest .
```

**Executar container:**

```bash
docker run -p 8002:8002 --env-file .env report-service:latest
```

**Build com target específico:**

```bash
docker build --target runtime -t report-service:latest .
```

## Logging e Observabilidade

### Loguru

O projeto utiliza **Loguru** para logging estruturado com contexto

Logs são formatados com cores no terminal e estruturados em JSON para máquinas.

### New Relic Integration

O serviço envia dados para New Relic automaticamente via agentes:
- **APM**: Traces de requisições e eventos customizados
- **Infrastructure**: Métricas de sistema e container
- **Custom Events**: Métricas específicas da aplicação (geração de relatórios, tempos, etc.)

Configure `NEW_RELIC_LICENSE_KEY` e `NRIA_LICENSE_KEY` para ativar.

### Métricas Customizadas

O `MetricsRecorder` em `observability/metrics.py` registra:
- Tempo de geração de relatório
- Contagem de relatórios gerados
- Falhas na geração

## Estrutura de Código

### Convenções Adotadas

- **Clean Architecture**: Camadas bem definidas com dependências apontando para o centro
- **Ports & Adapters**: Interfaces abstratas para inversão de controle
- **Pydantic**: Único framework externo permitido no Domain
- **Async/Await**: Todas as operações I/O são assíncronas
- **Type Hints**: Obrigatórios em todas as funções e métodos
- **Docstrings**: Descrevem propósito, parâmetros e retorno
- **PEP 8**: Nomes em snake_case (funções/variáveis) e PascalCase (classes)

### Sem Prints

Proibido usar `print()` em código de produção. Sempre use:

```python
from src.infrastructure.observability import get_logger
logger = get_logger()
logger.info("mensagem", extra_field=value)
```

### Sem Funções Aninhadas

Funções auxiliares são definidas no escopo do módulo ou como métodos privados (prefixo `_`), não aninhadas dentro de outras funções.

## Suporte e Contribuição

Para dúvidas, bugs ou sugestões:

1. Consulte a documentação do projeto principal
2. Abra uma issue no repositório
3. Entre em contato com a equipe de arquitetura
