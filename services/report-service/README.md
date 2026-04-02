# Report Service

Serviço responsável por consumir eventos de análise concluída via RabbitMQ, gerar relatórios estruturados e persistir em PostgreSQL, disponibilizando-os através de uma API REST.

## Estrutura do Projeto

```
services/report-service/
├── src/                                  # Código-fonte da aplicação
│   ├── domain/                          # Camada de Domínio (regras de negócio)
│   │   ├── entities/                    # Entidades: Relatorio
│   │   ├── events.py                    # Eventos de domínio: AnaliseConcluida, RelatorioGerado
│   │   ├── exceptions.py                # Exceções customizadas de domínio
│   │   └── repositories/                # Interfaces (Ports) de repositórios
│   │       └── relatorio_repository.py  # Contrato de persistência
│   │
│   ├── application/                     # Camada de Aplicação (casos de uso)
│   │   ├── use_cases/                   # Casos de uso: GenerateReport, GetReport
│   │   ├── dtos/                        # Data Transfer Objects
│   │   │   └── relatorio_response.py    # Resposta padronizada de relatório
│   │   └── ports/                       # Interfaces (Ports)
│   │       └── event_publisher.py       # Contrato para publicação de eventos
│   │
│   ├── infrastructure/                  # Camada de Infraestrutura (detalhes técnicos)
│   │   ├── database/                    # Conexão e sessões SQLAlchemy async
│   │   │   ├── session.py               # Configuração de conexão async
│   │   │   └── __init__.py
│   │   ├── models/                      # Modelos SQLAlchemy (mapeamento de tabelas)
│   │   │   ├── base.py                  # Classe base para modelos
│   │   │   ├── relatorio_model.py       # Modelo ORM para Relatorio
│   │   │   └── __init__.py
│   │   ├── messaging/                   # RabbitMQ (pub/sub)
│   │   │   ├── consumer.py              # Consumidor de eventos AnaliseConcluida
│   │   │   ├── publisher.py             # Publicador de eventos RelatorioGerado
│   │   │   ├── shared.py                # Instância global do publisher
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
│   │   │   │   ├── relatorio_controller.py  # Endpoints: GET /relatorios/{analise_id}
│   │   │   │   └── __init__.py
│   │   │   ├── health_controller.py     # Health check
│   │   │   └── __init__.py
│   │   ├── gateways/                    # Implementações concretas (Adapters)
│   │   │   ├── relatorio_repository_gateway.py   # SQLAlchemy adapter para Relatorio
│   │   │   ├── event_publisher_gateway.py        # RabbitMQ adapter para pub/sub
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
│   ├── test_domain/                     # Testes de entidades
│   ├── test_application/                # Testes de casos de uso (mocks de Ports)
│   ├── test_interface/                  # Testes de controllers (integração HTTP)
│   └── __init__.py
│
├── pyproject.toml                       # Configuração do projeto (uv, pytest, ruff)
├── alembic.ini                          # Configuração das migrações
├── newrelic.ini                         # Configuração do New Relic
├── Dockerfile                           # Build multistage (builder + runtime)
├── docker-compose.yml                   # Orquestração local (app, DB, RabbitMQ)
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
cd services/report-service
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

Certifique-se de que PostgreSQL e RabbitMQ estão rodando:

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

A aplicação estará disponível em `http://localhost:8000`.

#### Opção B: Docker Compose

```bash
docker-compose up -d
```

Isso inicia:
- **report-service**: Porta 8000
- **PostgreSQL**: Porta 5432 (volume persistente)
- **RabbitMQ**: Porta 5672 (management UI na porta 15672)

Para visualizar logs:

```bash
docker-compose logs -f report-service
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

### Verificação de tipos (ty)

```bash
uv run ty
```

## Endpoints da API

### GET /api/v1/relatorios/{analise_id}

Recupera um relatório gerado para uma análise específica.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "analise_id": "660e8400-e29b-41d4-a716-446655440001",
  "titulo": "Relatório de Análise Arquitetural",
  "conteudo": {
    "resumo": "Análise da arquitetura do sistema...",
    "componentes": [...],
    "padroes": [...],
    "recomendacoes": [...]
  },
  "criado_em": "2026-03-30T10:15:30Z",
  "atualizado_em": "2026-03-30T10:16:00Z"
}
```

**Erros:**
- `404 Not Found`: Relatório não encontrado para a análise especificada
- `500 Internal Server Error`: Erro ao recuperar o relatório

### GET /health

Health check que valida conexões com dependências (DB, RabbitMQ).

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
- **Entities**: `Relatorio` — objeto com identidade única, contém os dados do relatório gerado
- **Events**: `AnaliseConcluida`, `RelatorioGerado` — eventos de domínio
- **Exceptions**: Erros customizados de negócio
- **Ports (Interfaces)**: `RelatorioRepository`, `EventPublisher` — contratos abstratos

**Dependências externas permitidas**: Apenas `pydantic` (para validação e modelagem).

### 2. Application (Casos de Uso)

Implementa os cenários de negócio:
- **Use Cases**: `GenerateReport` (consome evento e gera relatório), `GetReport` (recupera relatório)
- **DTOs**: `RelatorioResponse` — dados para saída
- **Ports (Interfaces)**: `EventPublisher` — contrato para publicação de eventos

Depende do Domain, mas nunca de implementações concretas de infraestrutura.

### 3. Infrastructure (Detalhes Técnicos)

Implementações concretas de conexões externas:
- **Database**: SQLAlchemy async, migrações com Alembic
- **Messaging**: RabbitMQ (consumidor de `AnaliseConcluida`, publicador de `RelatorioGerado`)
- **Models**: Mapeamento ORM das tabelas

### 4. Interface (Adapters)

Adapta as camadas internas aos protocolos externos:
- **Controllers**: Rotas FastAPI que delegam para use cases
- **Gateways**: Implementações concretas dos Ports (ex: `SQLAlchemyRelatorioRepository`, `RabbitMQEventPublisherGateway`)
- **Presenters**: Formatadores de respostas HTTP

### Fluxo de Processamento

```
1. RabbitMQ Consumer recebe AnaliseConcluida
   ↓
2. GenerateReport.execute() (Use Case)
   ↓
3. Valida dados da análise (Domain logic)
   ↓
4. Monta estrutura do relatório (Domain logic)
   ↓
5. Persiste via SQLAlchemyRelatorioRepository (Adapter → Infra)
   ↓
6. Publica RelatorioGerado via RabbitMQEventPublisher (Adapter → Infra)
```

### Inversão de Dependência (Ports & Adapters)

Use cases injetam Ports (interfaces abstratas), não Adapters (implementações concretas):

```python
# Correto: Use case depende de Ports, implementações são injetadas
use_case = GenerateReport(
    relatorio_repository=SQLAlchemyRelatorioRepository(session),  # Implementação
    event_publisher=RabbitMQEventPublisherGateway(),             # Implementação
)
```

Testes unitários usam mocks dos Ports, nunca acessam banco real:

```python
# Mock de Port
class MockRelatorioRepository(RelatorioRepository):
    async def salvar(self, relatorio: Relatorio) -> Relatorio:
        # Implementação fake
        pass

# Teste injeta mock
use_case = GenerateReport(
    relatorio_repository=MockRelatorioRepository(),
    # ...
)
```

## Variáveis de Ambiente

Veja `env.example` para a lista completa. As principais:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DATABASE_HOST` | localhost | Host PostgreSQL |
| `DATABASE_PORT` | 5432 | Porta PostgreSQL |
| `DATABASE_USER` | report_user | Usuário DB |
| `DATABASE_PASSWORD` | report_pass | Senha DB |
| `DATABASE_NAME` | report_db | Nome do banco |
| `RABBITMQ_HOST` | localhost | Host RabbitMQ |
| `RABBITMQ_PORT` | 5672 | Porta RabbitMQ |
| `RABBITMQ_EXCHANGE_NAME` | analise.events | Exchange para publicação/consumo |
| `RABBITMQ_QUEUE_NAME` | report-service.reports | Fila de consumo de eventos |
| `DEBUG` | false | Ativa modo debug |
| `LOG_LEVEL` | INFO | Nível de log (DEBUG, INFO, WARNING, ERROR) |

## Recursos Adicionais

- **Logging**: Utiliza `structlog` com contexto estruturado
- **Monitoramento**: Integração com New Relic (`newrelic`)
- **Validação**: Pydantic para tipos e validação automática
- **Async/Await**: Operações totalmente assíncronas com asyncpg e aio-pika

## Suporte

Para dúvidas ou problemas, consulte a documentação do projeto principal ou entre em contato com a equipe de arquitetura.
