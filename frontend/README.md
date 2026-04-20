# ArchLens Frontend

SPA (React 18 + TypeScript + Vite) para ArchLens — ferramenta de análise arquitetural de diagramas. Usuários fazem upload de imagens/PDFs de diagramas, e o frontend orquestra o fluxo de análise, polling de status e exibição de relatórios em markdown com componentes identificados e riscos por severidade.

## Estrutura do Projeto

```
frontend/
├── src/
│   ├── config/
│   │   ├── env.ts              # Variáveis de ambiente (Kong, Clerk)
│   │   └── tokens.ts           # Tokens de design (cores, tipografia)
│   ├── services/
│   │   ├── httpClient.ts       # Axios + injeção de token (Clerk), port para autenticação
│   │   └── analysisService.ts  # Orquestração de chamadas API (upload, status, relatório)
│   ├── hooks/
│   │   ├── useAuthSetup.ts     # Inicializa provider de token (adapter Clerk)
│   │   └── useAnaliseStatus.ts # Hook de polling para status de análise
│   ├── types/
│   │   ├── AnaliseStatus.ts    # "recebido" | "processando" | "analisado" | "erro"
│   │   ├── AnaliseResponse.ts  # Status + metadados de análise
│   │   ├── AnalysisResult.ts   # Relatório estruturado (componentes, riscos)
│   │   ├── UploadResponse.ts   # ID de análise retornado no POST
│   │   ├── DownloadResponse.ts # URL presigned S3
│   │   └── RiskSeverity.ts     # Enumeração crítico/alto/médio/baixo
│   ├── components/
│   │   ├── ui/                 # Componentes agnósticos (Button, TextField, Pill)
│   │   ├── analysis/           # Upload, status cards, breakdown, renderização markdown
│   │   └── auth/               # SignInScreen, diagrama visual (Clerk)
│   ├── pages/
│   │   ├── NewAnalysisPage.tsx # Formulário de upload (validação, submit)
│   │   ├── ResultsPage.tsx     # Polling + exibição de relatório
│   │   └── helpers/
│   │       └── formatReport.ts # Utilitários de formatação de markdown
│   ├── App.tsx                 # Router lógico (SignedIn/Out), state de página
│   ├── main.tsx                # Entry point com ClerkProvider
│   └── index.css               # Estilos globais
├── Dockerfile                  # Multistage: builder (npm build) + nginx runtime
├── nginx.conf                  # SPA router + proxy /api → Kong, /s3 → LocalStack
├── vite.config.ts             # Alias @, proxy /s3 para dev local
├── tsconfig.json              # ES2020, strict: true, path aliases
├── env.example                # Variáveis obrigatórias (Kong, Clerk)
└── package.json               # React 18, Clerk, Axios, Vite
```

### Padrão de Arquitetura: Ports & Adapters

- **Port (Interface abstrata):** `httpClient.setTokenProvider()` define o contrato para injeção de tokens.
- **Adapter (Implementação concreta):** `useAuthSetup()` registra a função `getToken()` do Clerk como provider.
- **Benefício:** Axios interceptor fica desacoplado da autenticação; tokens são injetados dinamicamente antes de cada requisição.

## Pré-requisitos

- Node.js 24+
- npm 10+ (ou equivalente)
- Docker e Docker Compose (opcional, para executar com os serviços backend)
- Credenciais Clerk (publicable key + template JWT)
- URL da Kong API Gateway

## Configuração Local

### 1. Instalar Dependências

```bash
cd frontend
npm install
```

### 2. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e preencha com seus valores:

```bash
cp env.example .env.local
```

Edite `.env.local` com:

```env
VITE_KONG_BASE_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...seu_public_key_do_clerk...
VITE_CLERK_JWT_TEMPLATE=archlens
```

**Variáveis:**
- `VITE_KONG_BASE_URL`: URL base da Kong (em dev local: `http://localhost:8000`; em Docker: `/api`)
- `VITE_CLERK_PUBLISHABLE_KEY`: Chave pública do Clerk (obrigatória)
- `VITE_CLERK_JWT_TEMPLATE`: Template JWT customizado no Clerk (opcional, padrão: sem template)

### 3. Iniciar em Desenvolvimento

```bash
npm run dev
```

Acesso: http://localhost:5173

A aplicação proxy `/s3` para `http://localhost:4566` (LocalStack) e `/api` reescreve para `VITE_KONG_BASE_URL` (configurável em vite.config.ts).

### 4. Build para Produção

```bash
npm run build
```

Saída: `frontend/dist/` (pronto para servir via nginx ou deploy estático)

### 5. Preview de Build Local

```bash
npm run preview
```

Simula servidor estático em http://localhost:4173.

## Execução com Docker Compose

Do diretório raiz do projeto (`ArchLens/`):

```bash
docker compose up -d --build frontend
```

**O que acontece:**
1. Node 24 instala dependências e roda `npm run build` (Vite).
2. Nginx 1.27 (Alpine) serve `/app/dist/` na porta 8080.
3. Nginx proxy:
   - `/api/` → Kong (`http://kong:8000`)
   - `/s3/` → LocalStack (`http://localstack:4566`)
4. SPA fallback: qualquer rota não estática retorna `index.html`.

Acesso: http://localhost:8080 (ou seu host Docker)

## Fluxo de Análise (Frontend)

### 1. Upload (NewAnalysisPage)

```
POST /api/v1/analises (multipart/form-data)
├─ file: File (máx 10 MB, PNG/JPG/PDF)
└─ Retorna: { analise_id: "uuid" }
```

Validações frontend:
- MIME types: `image/png`, `image/jpeg`, `application/pdf`
- Extensões: `.png`, `.jpg`, `.jpeg`, `.pdf`
- Tamanho máximo: 10 MB

### 2. Polling de Status (ResultsPage + useAnaliseStatus)

```
GET /api/v1/analises/{analise_id}
Intervalo: 2s
Aguarda: status = "analisado" ou "erro"
```

Estados possíveis:
- `recebido`: Arquivo aceito, aguardando processamento
- `processando`: Análise em progresso
- `analisado`: Sucesso, relatório disponível
- `erro`: Falha no processamento

### 3. Obter Relatório (ResultsPage)

```
GET /api/v1/relatorios/{analise_id}
Retorna: { componentes: [...], riscos_por_severidade: {...}, markdown_url: "..." }
```

### 4. Download de Relatório (via S3 Presigned)

```
GET /api/v1/analises/{analise_id}/relatorio/download
Retorna: { download_url: "http://localstack:4566/..." }

Fetch: GET /s3/... (nginx reescreve para /s3/ → LocalStack)
```

A SPA busca markdown diretamente da URL presigned S3 e renderiza via React component.

## Testes e Linting

### Linting (ESLint)

```bash
npm run lint
```

Verifica padrões TS/TSX em `src/` conforme `.eslintrc` (se configurado).

### Type Checking (TypeScript Compiler)

```bash
npm run build
```

Já inclui `tsc -b` antes de Vite, checando tipos estritamente.

## Variáveis de Ambiente (Build-time)

As variáveis Vite (`VITE_*`) são interpoladas **em tempo de build** no HTML/JS.

**Em desenvolvimento:**
- Vite lê `.env.local` automaticamente
- HMR recarrega ao mudar variáveis

**Em Docker (Multistage):**
- Stage 1 (builder): Aceita `ARG` do `docker compose` via `build.args`
- Stage 2 (runtime): Nginx serve dist estático (variáveis já compiladas)

Exemplo docker-compose.yml:
```yaml
frontend:
  build:
    context: .
    dockerfile: frontend/Dockerfile
    args:
      VITE_KONG_BASE_URL: /api
      VITE_CLERK_PUBLISHABLE_KEY: pk_test_...
      VITE_CLERK_JWT_TEMPLATE: archlens
```

## Segurança (Nginx)

O `nginx.conf` implementa:
- **CSP (Content-Security-Policy):** Autoriza Clerk, bloqueia inline scripts não confiáveis
- **Security Headers:** X-Frame-Options, X-Content-Type-Options, HSTS, Referrer-Policy
- **SameSite Cookies:** Cookies do Clerk marcados `Secure; HttpOnly; SameSite=None`
- **Tamanho máximo de upload:** 10 MB (`client_max_body_size`)
- **Cache:** Assets hashados (1 ano); HTML (no-store)

## Troubleshooting

### "VITE_KONG_BASE_URL não configurada"

Verifique `.env.local` ou variáveis do ambiente. Em Docker, confirme build args no `docker-compose.yml`.

### "Sessão expirada ou não autorizada"

Token do Clerk expirou. Frontend captura `UnauthorizedError` (status 401) e notifica usuário para fazer login novamente.

### Erro no upload ou polling

Confirme que Kong está rodando (`docker compose ps`) e que `/api/v1/analises` está mapeado corretamente no Kong.

## Estrutura de Tipos

Tipos TypeScript key:
- **AnaliseStatus:** Union type (`"recebido" | "processando" | "analisado" | "erro"`)
- **AnaliseResponse:** `{ id, status, created_at, metadata }`
- **AnalysisResult:** `{ componentes: [], riscos_por_severidade: {}, markdown_url }`
- **ApiError / UnauthorizedError:** Custom error classes para tratamento específico

## Injeção de Dependência (Token)

**Como funciona:**

1. `App.tsx` monta `useAuthSetup()`
2. Hook obtém `getToken()` do Clerk (`useAuth`)
3. Hook injeta via `setTokenProvider(getToken)`
4. Axios interceptor (request) aguarda `tokenGetter()` e injeta `Authorization: Bearer`

Vantagem: HttpClient fica **agnóstico** a Clerk; fácil trocar provider (ex: OAuth2, API keys).

## Recursos Adicionais

- [Vite Documentation](https://vitejs.dev/)
- [React 18 Docs](https://react.dev/)
- [Clerk React SDK](https://clerk.com/docs/references/react)
- [Axios](https://axios-http.com/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
