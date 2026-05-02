# Executando o ArchLens Localmente

Este guia cobre tudo o que é necessário para subir o stack completo do ArchLens (Frontend, Serviços de Backend, Kong API Gateway e infraestrutura compartilhada) usando Docker Compose.

---

## Pré-requisitos

| Ferramenta | Versão | Finalidade |
|------------|--------|------------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | ≥ 26 | Runtime de containers |
| [Docker Compose](https://docs.docker.com/compose/) | ≥ 2.24 | Orquestração multi-container (incluído no Docker Desktop) |
| Conta no [Clerk](https://clerk.com) | — | Provedor de autenticação do frontend |
| Chave de API do [Google AI Studio](https://aistudio.google.com/app/apikey) | — | Backend de LLM (modelos Gemini via LiteLLM) |

> **Nota:** Todos os serviços Python utilizam `uv` internamente dentro do Docker. Não é necessário ter `uv`, `python` ou `node` instalados localmente para rodar o stack via Docker Compose.

---

## 1. Configuração de Ambiente

O projeto requer dois arquivos `.env`: um na raiz (infraestrutura + serviços) e um dentro de `frontend/` (variáveis de build do Vite).

### 1.1 `.env` da Raiz

Crie o arquivo a partir do template:

```bash
cp env.example .env
```

Preencha os valores obrigatórios:

```dotenv
# -- LLM (obrigatório) --
GEMINI_API_KEY=AIza...          # De https://aistudio.google.com/app/apikey

# -- LiteLLM Proxy (obrigatório) --
LITELLM_MASTER_KEY=sk-master-key-troque-aqui   # Qualquer string; usada para administrar o LiteLLM
LITELLM_API_KEY=sk-internal-key-troque-aqui    # Qualquer string; usada pelos serviços de backend

# -- Kong JWT Auth (opcional) --
# Se definido, o Kong exigirá autenticação JWT em todas as rotas de API.
# Deixe vazio para rodar sem autenticação (recomendado na configuração inicial).
KONG_JWT_SECRET=

# -- New Relic (opcional) --
# Deixe vazio para desabilitar o monitoramento de infraestrutura e APM.
NRIA_LICENSE_KEY=
```

> **Chaves do LiteLLM:** Os valores de `LITELLM_MASTER_KEY` e `LITELLM_API_KEY` são strings arbitrárias que você define. O mesmo valor de `LITELLM_API_KEY` deve ser configurado como `LLM_API_KEY` em cada arquivo `.env` de serviço (veja [1.2](#12-env-dos-serviços)).

### 1.2 `.env` dos Serviços

Cada serviço de backend possui seu próprio arquivo `.env`. Copie a partir dos exemplos fornecidos:

```bash
cp services/upload-service/env.example     services/upload-service/.env
cp services/processing-service/env.example services/processing-service/.env
cp services/report-service/env.example     services/report-service/.env
```

Os valores padrão já funcionam para desenvolvimento local. O único valor que você **deve** atualizar é a chave de API do LLM, para que corresponda ao que foi definido no passo 1.1:

```dotenv
# Em services/processing-service/.env e services/report-service/.env
LLM_API_KEY=sk-internal-key-troque-aqui   # Deve ser igual ao LITELLM_API_KEY do .env da raiz
```

### 1.3 `.env.local` do Frontend

```bash
cp frontend/env.example frontend/.env.local
```

```dotenv
# -- API Gateway (aponta para o Kong local por padrão) --
VITE_KONG_BASE_URL=http://localhost:8000

# -- Autenticação Clerk (obrigatório) --
# Obtenha em https://dashboard.clerk.com → seu app → API Keys
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...

# -- Template JWT do Clerk (opcional) --
# Necessário apenas quando KONG_JWT_SECRET estiver definido. Crie um JWT Template no
# Clerk Dashboard → JWT Templates e cole o nome dele aqui.
VITE_CLERK_JWT_TEMPLATE=
```

---

## 2. Build e Subida do Stack

### Primeira execução (ou após mudanças em dependências)

```bash
docker compose up --build -d
```

Esse comando irá:
1. Fazer o build de todas as imagens (serviços Python via `uv`, frontend via Vite + Nginx).
2. Iniciar a infraestrutura compartilhada (PostgreSQL, RabbitMQ, LocalStack, LiteLLM, Kong).
3. Executar as migrations do banco de dados via Alembic em containers dedicados.
4. Iniciar os três serviços de backend e o frontend.

### Execuções seguintes (sem alterações de código)

```bash
docker compose up -d
```

### Rebuild de um único serviço

```bash
docker compose up --build -d <nome-do-servico>
# Exemplos:
docker compose up --build -d upload-service
docker compose up --build -d frontend
```

### Parar tudo

```bash
docker compose down
```

Para remover também os volumes (apaga os dados do banco e do S3):

```bash
docker compose down -v
```

---

## 3. Mapa de Serviços

Com o stack no ar, os seguintes endpoints ficam disponíveis em `localhost`:

| Serviço | URL | Observações |
|---------|-----|-------------|
| **Frontend** | http://localhost:8091 | React SPA servido pelo Nginx |
| **Kong Proxy** | http://localhost:8000 | Entrypoint público da API |
| **Kong Admin API** | http://localhost:8001 | Admin REST (para inspecionar rotas) |
| **Kong Admin UI** | http://localhost:8002 | Dashboard web |
| **Upload Service** | http://localhost:8010 | Acesso direto (sem passar pelo Kong) |
| **Processing Service** | http://localhost:8011 | Acesso direto |
| **Report Service** | http://localhost:8012 | Acesso direto |
| **LiteLLM Proxy** | http://localhost:4000 | Gateway de LLM |
| **RabbitMQ Management** | http://localhost:15672 | Credenciais padrão: `archlens` / `archlens_dev` |
| **LocalStack S3** | http://localhost:4566 | Emulação da API AWS |
| **PostgreSQL** | `localhost:5432` | Quatro bancos de dados (veja abaixo) |

### Bancos de Dados PostgreSQL

| Banco | Usuário | Senha |
|-------|---------|-------|
| `upload_db` | `upload_user` | `upload_pass` |
| `processing_db` | `processing_user` | `processing_pass` |
| `report_db` | `report_user` | `report_pass` |
| `litellm_db` | `litellm_user` | `litellm_pass` |

---

## 4. Verificação do Stack

Execute essas verificações após o `docker compose up`:

### 4.1 Todos os containers estão rodando

```bash
docker compose ps
```

Todos os serviços devem exibir o status `running`. Os containers de migration (`*-migrations`) estarão com `exited (0)` — isso é esperado.

### 4.2 Frontend

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8091
# Esperado: 200
```

Ou abra http://localhost:8091 no navegador. A tela de login do Clerk deve aparecer.

### 4.3 Kong Proxy

```bash
curl http://localhost:8000/upload
# Esperado: {"status":"ok","service":"upload-service"}
```

### 4.4 Kong Admin API

```bash
curl http://localhost:8001/
# Esperado: JSON com informações de versão do Kong
```

Para listar todas as rotas registradas:

```bash
curl http://localhost:8001/routes | python3 -m json.tool
```

### 4.5 Serviços de Backend (acesso direto)

```bash
curl http://localhost:8010/health   # upload-service
curl http://localhost:8011/health   # processing-service
curl http://localhost:8012/health   # report-service
# Esperado: {"status":"ok"} para cada um
```

### 4.6 RabbitMQ

Acesse http://localhost:15672 e faça login com `archlens` / `archlens_dev`. A exchange `analise.events` e as três filas dos serviços devem aparecer em **Exchanges** e **Queues**.

### 4.7 LiteLLM

```bash
curl http://localhost:4000/health
# Esperado: JSON com o status de saúde dos modelos
```

---

## 5. Autenticação no Kong

O Kong opera em dois modos, dependendo se `KONG_JWT_SECRET` está definido no `.env`:

| `KONG_JWT_SECRET` | Modo | Comportamento |
|-------------------|------|---------------|
| Vazio | **Sem autenticação** | Todas as rotas da API ficam abertas. Indicado para a configuração inicial. |
| Qualquer string | **Auth JWT** | Todas as rotas `/v1/*` exigem um JWT válido assinado pelo Clerk no header `Authorization: Bearer <token>`. |

Para habilitar a autenticação, defina `KONG_JWT_SECRET` no `.env` e configure `VITE_CLERK_JWT_TEMPLATE` no `frontend/.env.local` com o nome de um JWT Template criado no seu Clerk Dashboard. Em seguida, reinicie o Kong:

```bash
docker compose up -d --no-deps kong
```

---

## 6. Logs

Acompanhar logs de um serviço específico:

```bash
docker compose logs -f upload-service
docker compose logs -f kong
docker compose logs -f frontend
```

Acompanhar todos os serviços de uma vez:

```bash
docker compose logs -f
```

---

## 7. Problemas Comuns

### Migrations falham na primeira subida

O PostgreSQL pode não estar totalmente pronto quando os containers de migration iniciam. Execute novamente:

```bash
docker compose up -d
```

O Docker Compose reiniciará apenas os containers que falharam e o banco já estará pronto.

### Porta já em uso

Se um conflito de porta for reportado, localize e encerre o processo conflitante:

```bash
# Linux/macOS
lsof -i :<porta>

# Windows (PowerShell)
netstat -ano | findstr :<porta>
```

### Windows: containers encerram imediatamente sem erro

Quase sempre é um problema de quebra de linha CRLF. Certifique-se de que o Git está convertendo as quebras de linha corretamente, ou execute:

```bash
dos2unix gateways/kong/docker-entrypoint.sh
dos2unix services/*/docker/postgres/init.sh
```

### LiteLLM retorna erros de modelo

Verifique se sua `GEMINI_API_KEY` é válida e possui cota disponível. O modelo em uso é `gemini-2.0-flash-lite` (com `gemini-2.5-flash` como fallback). Confira os logs do LiteLLM:

```bash
docker compose logs -f litellm
```
