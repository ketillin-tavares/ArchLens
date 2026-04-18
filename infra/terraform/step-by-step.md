# ArchLens — Guia de Deploy Terraform Cloud

Passo a passo completo para provisionar toda a infraestrutura AWS do ArchLens
usando os 3 workspaces encadeados no Terraform Cloud.

---

## Pré-requisitos

| Recurso | Detalhes |
|---------|---------|
| Conta AWS | Com permissões de administrador (IAM, VPC, EKS, RDS, S3, ECR, ELB) |
| Terraform Cloud | Organização `archlens` criada em [app.terraform.io](https://app.terraform.io) |
| Terraform CLI | >= 1.5 instalado localmente (apenas para `terraform login`) |
| AWS CLI v2 | Para configurar credenciais e acessar o cluster EKS após deploy |
| kubectl | Para aplicar manifests K8s (Kong, Vault bootstrap) |
| Helm | Para debug local (opcional) |
| GitHub | Repositório com os secrets configurados para CI/CD |

---

## Etapa 0 — Configurar Terraform Cloud

### 0.1 — Login

```bash
terraform login
```

### 0.2 — Criar os 3 workspaces

No Terraform Cloud, crie os workspaces **na ordem**:

| # | Workspace | Working Directory |
|---|-----------|------------------|
| 1 | `archlens-foundation` | `infra/terraform/01-foundation` |
| 2 | `archlens-cluster` | `infra/terraform/02-cluster` |
| 3 | `archlens-platform` | `infra/terraform/03-platform` |

**Settings de cada workspace:**
- **Workflow:** **CLI-driven** (obrigatório) — o `terraform apply` é disparado pelo GitHub Actions (`.github/workflows/infra-deploy.yaml`) ou pela CLI local, e o TFC só armazena state + executa remoto. Não use VCS-driven: a ordenação `01 → 02 → 03` é controlada pelo pipeline (03 lê outputs de 01/02 via `terraform_remote_state`), e o pipeline ainda roda passos não-Terraform (`kubectl`, `helm`, bootstrap do Vault) entre os workspaces.
- **Execution Mode:** Remote
- **Apply Method:** Manual (recomendado em produção) ou Auto
- **Terraform Version:** >= 1.5

> **Por que CLI-driven e não VCS-driven?** Com VCS-driven cada workspace dispara sozinho em qualquer push que toque o path — você perde a ordem entre os 3 workspaces e não consegue intercalar os passos de `kubectl`/`vault`/`helm`. Com CLI-driven o pipeline controla tudo.

### 0.3 — Configurar credenciais AWS

No Terraform Cloud, vá em **Settings > Variable Sets** e crie um variable set
compartilhado entre os 3 workspaces:

| Variável | Tipo | Valor |
|----------|------|-------|
| `AWS_ACCESS_KEY_ID` | Environment, Sensitive | Sua access key |
| `AWS_SECRET_ACCESS_KEY` | Environment, Sensitive | Sua secret key |
| `AWS_DEFAULT_REGION` | Environment | `us-east-2` |

### 0.4 — Configurar secrets no GitHub (CI/CD)

Os workflows em `.github/workflows/` precisam de apenas **3 secrets** no repositório
(`Settings > Secrets and variables > Actions > Repository secrets`). Todos os
demais valores sensíveis (db_password, rabbitmq_password, newrelic_license_key,
litellm_db_password, etc.) vivem no **Terraform Cloud Variable Set** — não em GH.

| Secret | Usado em | Por quê |
|--------|----------|---------|
| `TF_API_TOKEN` | `infra-deploy.yaml` (todos os jobs Terraform) | Autentica a CLI no TFC via `hashicorp/setup-terraform` (`cli_config_credentials_token`). Gerar em **TFC > User Settings > Tokens** com escopo de team que tenha acesso aos 3 workspaces. |
| `AWS_ACCESS_KEY_ID` | `infra-deploy.yaml` (job `k8s-manifests`) e `services-deploy.yaml` (build + deploy) | Usado por `aws-actions/configure-aws-credentials` para rodar `aws eks update-kubeconfig`, push no ECR e `kubectl apply`/`kubectl set image`. |
| `AWS_SECRET_ACCESS_KEY` | `infra-deploy.yaml` (job `k8s-manifests`) e `services-deploy.yaml` | Par da access key acima. |
| `SONAR_TOKEN` | `sonarcloud.yaml` (scan dos 3 services em push na main + dispatch manual) | Token de usuário gerado em **SonarCloud > My Account > Security**. Usado pelo `SonarSource/sonarqube-scan-action` para enviar coverage + análise estática ao projeto SonarCloud. Ver Etapa 0.5. |

**Repository variables (não-sensíveis):**

| Variable | Usada em | Por quê |
|----------|----------|---------|
| `SONAR_ORGANIZATION` | `sonarcloud.yaml` | Key (slug) da organização SonarCloud. Injetado via `-Dsonar.organization` + `-Dsonar.projectKey` para manter os `sonar-project.properties` agnósticos ao dono do fork. Ver Etapa 0.5. |

> **Mesma conta AWS:** as credenciais do GitHub podem ser as mesmas do Variable Set do TFC (conta com permissões de EKS/ECR/IAM). Em produção, recomenda-se usar **OIDC federado** (`aws-actions/configure-aws-credentials` com `role-to-assume`) no lugar de access keys estáticas — o `permissions: id-token: write` já está setado nos workflows para isso.

> **O que NÃO precisa estar no GitHub:** `db_password`, `rabbitmq_password`, `rabbitmq_erlang_cookie`, `newrelic_license_key`, `newrelic_account_id`, `litellm_db_password`, `GEMINI_API_KEY`, `LITELLM_MASTER_KEY`, `KONG_JWT_SECRET`. Esses vivem em TFC Variable Sets (Etapa 1/2/3) ou no Vault (Etapa 4).

### 0.5 — Configurar SonarCloud (quality gate em PRs)

O workflow `.github/workflows/sonarcloud.yaml` roda análise estática + coverage
nos 3 services **após merge na `main`** (trigger `push`) e também via
`workflow_dispatch` manual. Não roda em PRs — o Quality Gate age como
relatório pós-merge, não como gate bloqueante.

**Comportamento por trigger:**
- **`push` em `main`** — usa `dorny/paths-filter` pra só escanear services que
  tiveram alteração no commit (evita rodar scan completo quando só a infra mudou).
- **`workflow_dispatch`** — escaneia o service selecionado (ou `all`) **sempre**,
  independente de ter havido mudança. Útil pra re-analisar após ajuste de
  config/quality gate ou forçar um novo baseline.

Configure uma vez:

1. **Criar organização e importar o repo:**
   - Acesse [sonarcloud.io](https://sonarcloud.io) e faça login com GitHub.
   - Crie (ou use uma existente) a **Organização** — anote o **Key** (slug
     minúsculo, ex: `minha-org`). É ele que vai no `SONAR_ORGANIZATION`.
   - `+` > **Analyze new project** > selecione o repo `archlens`.
   - Importe **3 projetos** (um por service), com `projectKey` no formato
     `<org-key>_archlens-<svc>`:
     - `<org-key>_archlens-upload-service`
     - `<org-key>_archlens-processing-service`
     - `<org-key>_archlens-report-service`
   - Em cada projeto, escolha **"With GitHub Actions"** como método de análise
     (NÃO o Automatic Analysis — ele conflita com o scanner CI quando você tem
     `sonar-project.properties`).

2. **Gerar o `SONAR_TOKEN`:**
   - SonarCloud > **My Account > Security** > **Generate Token** com nome
     `github-actions-archlens` e expiração de 90 dias (ou mais).
   - Copie o token (só aparece uma vez).

3. **Adicionar secret + variable no GitHub:**
   - Repo > **Settings > Secrets and variables > Actions**.
   - Aba **Secrets** > **New repository secret**:
     - Name: `SONAR_TOKEN`, Value: o token copiado.
   - Aba **Variables** > **New repository variable**:
     - Name: `SONAR_ORGANIZATION`, Value: o **Key** da sua org SonarCloud.

4. **Configurar Quality Gate (opcional mas recomendado):**
   - SonarCloud > cada projeto > **Quality Gates** > use "Sonar way" (default)
     ou crie uma custom. A Quality Gate **não bloqueia merge** (o workflow
     não roda em PRs), mas o resultado aparece no dashboard SonarCloud
     de cada projeto — serve como termômetro pós-merge.

> **Agnóstico ao dono do fork:** `projectKey` e `organization` **não** ficam
> hardcoded nos `sonar-project.properties` — eles são injetados pelo workflow
> via `-D` lendo `${{ vars.SONAR_ORGANIZATION }}`. Fork do repo só precisa
> ajustar a variable + secret, sem tocar em código.

> **Arquivos envolvidos:** cada service tem seu `sonar-project.properties` em
> `services/<svc>/` (sources, tests, exclusões, versão Python, caminho do
> `coverage.xml`). O workflow detecta mudanças via `dorny/paths-filter` — só
> escaneia services que foram tocados no PR, economizando minutos de CI.

---

## Etapa 1 — Deploy `01-foundation`

Provisiona: VPC, Subnets, NAT Gateway, RDS PostgreSQL, S3, ECR, IAM Roles, Security Groups.

### 1.1 — Configurar variáveis do workspace

No workspace `archlens-foundation`, adicione as variáveis:

| Variável | Tipo | Obrigatório | Valor |
|----------|------|-------------|-------|
| `db_password` | Terraform, **Sensitive** | Sim | Senha forte para o RDS PostgreSQL |
| `newrelic_account_id` | Terraform, **Sensitive** | Sim | Account ID do New Relic (para AWS API polling) |
| `aws_region` | Terraform | Não | `us-east-2` (default) |
| `environment` | Terraform | Não | `dev` (default) |
| `rds_instance_class` | Terraform | Não | `db.t3.micro` (default, free tier) |
| `s3_expiration_days` | Terraform | Não | `30` (default) |

### 1.2 — Executar plan + apply

Há 3 formas de disparar o apply (todas usam o mesmo workspace CLI-driven):

```bash
# A) Via CLI local (bom para primeira vez / debug)
cd infra/terraform/01-foundation
terraform init
terraform plan
terraform apply

# B) Via Terraform Cloud UI: Runs > Start new run > Plan and apply

# C) Via GitHub Actions (recomendado para o fluxo recorrente):
#    workflow_dispatch em .github/workflows/infra-deploy.yaml com workspace=foundation
#    (o pipeline autentica no TFC via TF_API_TOKEN e executa remoto na ordem correta)
```

### 1.3 — Anotar outputs

Após o apply, anote os outputs — serão consumidos automaticamente via
`terraform_remote_state` pelos próximos workspaces:

```
vpc_id                       = "vpc-xxxxxxxxx"
rds_endpoint                 = "archlens-db.xxxxxx.us-east-2.rds.amazonaws.com:5432"
s3_bucket                    = "archlens-diagramas-xxxxxx"
ecr_urls                     = { upload = "...", processing = "...", report = "..." }
eks_cluster_role_arn         = "arn:aws:iam::xxxx:role/archlens-eks-cluster-role"
eks_nodes_role_arn           = "arn:aws:iam::xxxx:role/archlens-eks-nodes-role"
newrelic_integration_role_arn = "arn:aws:iam::xxxx:role/NewRelicInfrastructure-Integrations"
```

---

## Etapa 2 — Deploy `02-cluster`

Provisiona: EKS Cluster, Node Group (SPOT), OIDC Provider, ALB Controller, Namespaces, Service Accounts.

### 2.1 — Configurar variáveis do workspace

No workspace `archlens-cluster`:

| Variável | Tipo | Obrigatório | Valor |
|----------|------|-------------|-------|
| `aws_region` | Terraform | Não | `us-east-2` (default) |
| `environment` | Terraform | Não | `dev` (default) |
| `eks_cluster_version` | Terraform | Não | `1.29` (default) |
| `node_capacity_type` | Terraform | Não | `SPOT` (default, ~60% mais barato) |
| `node_min_size` | Terraform | Não | `2` (default) |
| `node_max_size` | Terraform | Não | `4` (default) |
| `node_desired_size` | Terraform | Não | `3` (default) — acomoda plataforma + sistema + 6 service pods em min com folga para HPA scale-up moderado |

### 2.2 — Executar plan + apply

```bash
cd infra/terraform/02-cluster
terraform init
terraform plan
terraform apply
```

> **Tempo estimado:** O EKS leva ~10-15 minutos para provisionar.

### 2.3 — Configurar kubectl

Após o apply, configure o acesso local ao cluster:

```bash
aws eks update-kubeconfig \
  --region us-east-2 \
  --name archlens-cluster
```

Verificar:

```bash
kubectl get nodes
kubectl get ns archlens
kubectl get sa -n archlens
```

### 2.4 — Atualizar OIDC no 01-foundation (IMPORTANTE)

O OIDC provider ID é criado junto com o EKS. Os IRSA roles no `01-foundation`
precisam desse valor para funcionar. Atualize o `oidc_provider` nos locals:

> **Sensibilidade:** o OIDC provider ID **não é sensível**. É um identificador público — aparece em IAM trust policies (que vão pro state) e em docs oficiais da AWS. Sozinho ele não concede acesso a nada: só funciona combinado com (a) a trust policy do IAM role, (b) uma ServiceAccount específica no cluster e (c) credenciais AWS válidas. Pode commitar no `main.tf` tranquilamente.

```bash
# Obter o OIDC issuer do cluster
aws eks describe-cluster \
  --name archlens-cluster \
  --query "cluster.identity.oidc.issuer" \
  --output text
# Saída: https://oidc.eks.us-east-2.amazonaws.com/id/ABCDEF1234567890
```

No arquivo `infra/terraform/01-foundation/main.tf`, atualize o placeholder:

```hcl
locals {
  oidc_provider = "oidc.eks.us-east-2.amazonaws.com/id/ABCDEF1234567890"
}
```

Depois, re-aplique o `01-foundation`:

```bash
cd infra/terraform/01-foundation
terraform plan   # deve mostrar mudança nos IRSA roles
terraform apply
```

---

## Etapa 3 — Deploy `03-platform`

Provisiona: Vault, RabbitMQ, Kong, LiteLLM, New Relic.

### 3.1 — Configurar variáveis do workspace

No workspace `archlens-platform`:

| Variável | Tipo | Obrigatório | Valor |
|----------|------|-------------|-------|
| `rabbitmq_password` | Terraform, **Sensitive** | Sim | Senha para o RabbitMQ (criada pelo chart Bitnami via `auth.password`) |
| `rabbitmq_erlang_cookie` | Terraform, **Sensitive** | Sim | `openssl rand -hex 32` |
| `newrelic_license_key` | Terraform, **Sensitive** | Sim | Ingest License Key do New Relic |
| `db_password` | Terraform, **Sensitive** | Sim | Mesma senha do RDS (para nri-postgresql e bootstrap do litellm_db) |
| `litellm_db_password` | Terraform, **Sensitive** | Sim | Senha do usuário `litellm_user` (criado no RDS pelo Job `litellm-db-bootstrap`) — equivalente ao `litellm_pass` do docker-compose |
| `vault_service_type` | Terraform | Não | `LoadBalancer` (default, bootstrap) |
| `litellm_image` | Terraform | Não | `ghcr.io/berriai/litellm:v1.83.2-nightly` (default, alinhada com `gateways/litellm/Dockerfile`) |
| `aws_region` | Terraform | Não | `us-east-2` (default) |
| `environment` | Terraform | Não | `dev` (default) |

> **Nota (RabbitMQ):** As definitions do RabbitMQ não declaram mais o usuário `archlens` (o chart Bitnami é quem o cria com a senha de `rabbitmq_password`). Após o apply, a senha pode ser recuperada via:
>
> ```bash
> terraform -chdir=infra/terraform/03-platform output -raw rabbitmq_password
> ```

### 3.2 — Executar plan + apply

```bash
cd infra/terraform/03-platform
terraform init
terraform plan
terraform apply
```

### 3.3 — Verificar os serviços

```bash
# Pods — deve listar: vault, rabbitmq, kong, litellm-proxy,
# presidio-analyzer, presidio-anonymizer
kubectl get pods -n archlens
kubectl get pods -n newrelic

# Job one-shot que cria litellm_db + litellm_user no RDS
kubectl get job litellm-db-bootstrap -n archlens
# COMPLETIONS deve ser 1/1 antes do litellm-proxy subir

# Services e LoadBalancers
kubectl get svc -n archlens

# Outputs do Terraform
terraform output
```

> **Guardrails LiteLLM:** os sidecars `presidio-analyzer` e `presidio-anonymizer` rodam como Deployments independentes no namespace `archlens` (imagens oficiais da Microsoft, porta 3000). O LiteLLM se conecta via `PRESIDIO_ANALYZER_API_BASE` e `PRESIDIO_ANONYMIZER_API_BASE` — mesmo padrão do docker-compose.

---

## Etapa 4 — Bootstrap do Vault

O Vault é provisionado em modo standalone (sealed). É necessário inicializá-lo
e popular os secrets antes que os serviços funcionem.

### 4.1 — Obter URL do Vault

```bash
# Se vault_service_type = "LoadBalancer"
export VAULT_ADDR=$(kubectl get svc vault -n archlens \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "http://${VAULT_ADDR}:8200"
```

### 4.2 — Inicializar o Vault

```bash
# Inicializar com 5 keys e threshold de 3
vault operator init \
  -key-shares=5 \
  -key-threshold=3

# SALVAR AS UNSEAL KEYS E O ROOT TOKEN EM LOCAL SEGURO!
```

### 4.3 — Unseal do Vault

```bash
# Usar 3 das 5 unseal keys
vault operator unseal <unseal-key-1>
vault operator unseal <unseal-key-2>
vault operator unseal <unseal-key-3>
```

### 4.4 — Popular secrets

```bash
export VAULT_TOKEN="<root-token>"

# Habilitar KV v2
vault secrets enable -version=2 -path=secret kv

# LiteLLM — chaves da API Gemini (mesmo provider do docker-compose)
# Obs: o LITELLM_DATABASE_URL eh montado pela TF a partir do RDS + litellm_db_password.
vault kv put secret/archlens/litellm \
  GEMINI_API_KEY="AIza..." \
  MASTER_KEY="lm-master-key-..."

# RabbitMQ — credenciais (usar o output do Terraform)
RABBITMQ_PASS=$(terraform -chdir=infra/terraform/03-platform output -raw rabbitmq_password)
vault kv put secret/archlens/rabbitmq \
  RABBITMQ_PASSWORD="${RABBITMQ_PASS}"

# Kong JWT — mesmo secret compartilhado com o docker-compose (KONG_JWT_SECRET).
# Gere uma string aleatoria forte (>=32 bytes) e guarde no Vault. Este secret
# eh usado tanto pelo Kong Ingress (Secret archlens-jwt-credential) quanto pelo
# gerador de tokens (gateways/kong/generate-jwt.py).
# Secrets dos 3 services — consumidos pelos Deployments via Vault Agent Injector
# (ver infra/k8s/deployments/*.yaml). O DATABASE_HOST sai do output do RDS.
RDS_HOST=$(terraform -chdir=infra/terraform/01-foundation output -raw rds_address)
S3_BUCKET=$(terraform -chdir=infra/terraform/01-foundation output -raw s3_bucket)
NR_LICENSE_KEY="<sua-license-key>"
NR_ACCOUNT_ID="<seu-account-id>"

vault kv put secret/archlens/upload \
  DATABASE_HOST="${RDS_HOST}" \
  DATABASE_USER="upload_user" \
  DATABASE_PASSWORD="<senha-upload>" \
  RABBITMQ_HOST="rabbitmq.archlens.svc.cluster.local" \
  RABBITMQ_PASSWORD="${RABBITMQ_PASS}" \
  S3_BUCKET_NAME="${S3_BUCKET}" \
  NEW_RELIC_LICENSE_KEY="${NR_LICENSE_KEY}" \
  NEW_RELIC_ACCOUNT_ID="${NR_ACCOUNT_ID}"

vault kv put secret/archlens/processing \
  DATABASE_HOST="${RDS_HOST}" \
  DATABASE_USER="processing_user" \
  DATABASE_PASSWORD="<senha-processing>" \
  RABBITMQ_HOST="rabbitmq.archlens.svc.cluster.local" \
  RABBITMQ_PASSWORD="${RABBITMQ_PASS}" \
  S3_BUCKET_NAME="${S3_BUCKET}" \
  LLM_API_KEY="sk-litellm" \
  NEW_RELIC_LICENSE_KEY="${NR_LICENSE_KEY}" \
  NEW_RELIC_ACCOUNT_ID="${NR_ACCOUNT_ID}"

vault kv put secret/archlens/report \
  DATABASE_HOST="${RDS_HOST}" \
  DATABASE_USER="report_user" \
  DATABASE_PASSWORD="<senha-report>" \
  RABBITMQ_HOST="rabbitmq.archlens.svc.cluster.local" \
  RABBITMQ_PASSWORD="${RABBITMQ_PASS}" \
  S3_BUCKET_NAME="${S3_BUCKET}" \
  LLM_API_KEY="sk-litellm" \
  NEW_RELIC_LICENSE_KEY="${NR_LICENSE_KEY}" \
  NEW_RELIC_ACCOUNT_ID="${NR_ACCOUNT_ID}"

# Kong JWT — mesmo secret compartilhado com o docker-compose (KONG_JWT_SECRET).
# Gere uma string aleatoria forte (>=32 bytes) e guarde no Vault. Este secret
# eh usado tanto pelo Kong Ingress (Secret archlens-jwt-credential) quanto pelo
# gerador de tokens (gateways/kong/generate-jwt.py).
KONG_JWT_SECRET=$(openssl rand -hex 32)
vault kv put secret/archlens/kong \
  KONG_JWT_SECRET="${KONG_JWT_SECRET}"

# RDS — credenciais
vault kv put secret/archlens/database \
  DB_HOST="<rds_address do output 01-foundation>" \
  DB_PORT="5432" \
  DB_NAME="archlens" \
  DB_USER="archlens" \
  DB_PASSWORD="<mesma-senha-do-terraform>"

# S3 — nome do bucket
vault kv put secret/archlens/s3 \
  BUCKET_NAME="<s3_bucket do output 01-foundation>"
```

### 4.5 — Configurar Kubernetes Auth

```bash
# Habilitar auth method kubernetes
vault auth enable kubernetes

# Configurar com o endpoint do cluster
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc.cluster.local:443"

# Criar policy para os serviços
vault policy write archlens-services - <<EOF
path "secret/data/archlens/*" {
  capabilities = ["read"]
}
EOF

# Criar role vinculada ao namespace archlens
vault write auth/kubernetes/role/archlens-services \
  bound_service_account_names="*" \
  bound_service_account_namespaces="archlens" \
  policies="archlens-services" \
  ttl="1h"
```

### 4.6 — Restringir acesso externo ao Vault

Após o bootstrap, altere o tipo do service para ClusterIP:

1. No Terraform Cloud, mude a variável `vault_service_type` para `ClusterIP`
2. Re-aplique o workspace `03-platform`

```bash
cd infra/terraform/03-platform
terraform plan   # deve mostrar mudança no service type
terraform apply
```

A partir deste ponto, o Vault só é acessível via:
- **Internamente:** `http://vault.archlens.svc.cluster.local:8200`
- **Externamente:** `kubectl port-forward svc/vault -n archlens 8200:8200`

---

## Etapa 5 — Aplicar manifests K8s (Deployments + Kong + HPA)

Os Deployments dos services, KongPlugins, Ingress resources, JWT credential e
HPAs são configurados via manifests K8s (não via Terraform):

### 5.0 — Deployments dos 3 services (com `resources` declarados)

```bash
# Imprescindivel ANTES do HPA — sem requests.cpu nos pods, o HPA fica <unknown>.
# Os manifests usam Vault Agent Injector para secrets (annotations), ConfigMap
# para env nao-sensivel e IRSA (upload-service-sa, processing-service-sa) para S3.
kubectl apply -f infra/k8s/deployments/

# Verificar
kubectl get deploy,svc -n archlens -l project=archlens
```

> **PLACEHOLDER nas imagens:** os manifests trazem `image: PLACEHOLDER/archlens/<svc>:latest` apenas como espaço-reservado (ECR está IMMUTABLE — `:latest` não é válido no push). A imagem real é setada pelo CI/CD na **Etapa 6** via `kubectl set image`. Antes do primeiro deploy você pode aplicar a imagem manualmente:
>
> ```bash
> ECR=<account-id>.dkr.ecr.us-east-2.amazonaws.com
> for svc in upload-service processing-service report-service; do
>   kubectl set image deployment/$svc $svc=$ECR/archlens/$svc:v1.0.0 -n archlens
> done
> ```

### 5.1 — Kong (KongPlugins, Ingress, JWT credential) e HPA + PDB

```bash
# Kong: plugins, ingress, credencial JWT
# OBS: o Kong da cloud usa o MESMO metodo de auth do docker-compose (JWT HS256).
# Os 3 Ingresses (upload, report, processing) exigem Authorization: Bearer <token>.
kubectl apply -f infra/k8s/ingress/kong-config.yaml

# Injetar o KONG_JWT_SECRET (do Vault) no Secret `archlens-jwt-credential`.
# O manifest ja cria o Secret com um placeholder; aqui sobrescrevemos o campo `secret`
# com o valor real recuperado do Vault (mesmo secret usado no docker-compose).
KONG_JWT_SECRET=$(vault kv get -field=KONG_JWT_SECRET secret/archlens/kong)
kubectl create secret generic archlens-jwt-credential \
  -n archlens \
  --from-literal=algorithm=HS256 \
  --from-literal=key=archlens-issuer \
  --from-literal=secret="${KONG_JWT_SECRET}" \
  --dry-run=client -o yaml | \
  kubectl label --local -f - konghq.com/credential=jwt --dry-run=client -o yaml | \
  kubectl apply -f -

# HPA + PodDisruptionBudget: autoscaling e resiliencia dos 3 servicos
# Cada arquivo contem um HPA e um PDB (minAvailable=1) no mesmo manifest
kubectl apply -f infra/k8s/hpa/
```

> **HPA — limites atuais:**
> - `upload-service`: min=2, max=6
> - `processing-service`: min=2, max=2 (limitado pela capacidade do cluster `t3.medium`)
> - `report-service`: min=2, max=4 (minReplicas=2 evita ponto unico de falha)

Verificar:

```bash
# Plugins ativos
kubectl get kongplugin -n archlens

# Ingress resources
kubectl get ingress -n archlens

# HPA configurados
kubectl get hpa -n archlens

# URL pública do Kong
kubectl get svc kong-gateway-proxy -n archlens \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

> **Nota:** O HPA depende do **metrics-server** (instalado no workspace
> `02-cluster` via Helm). Sem ele, o HPA fica em estado `<unknown>` nas
> métricas de CPU/memória.

---

## Etapa 6 — Deploy dos serviços (CI/CD ou manual)

### Via CI/CD (GitHub Actions)

O workflow `services-deploy.yaml` faz build + scan + push + rollout automaticamente
ao fazer push de uma tag `v*` (ou via `workflow_dispatch`). O pipeline inclui:

- **BuildKit + cache** (`--cache-from` da tag `latest`) para acelerar builds incrementais
- **Trivy scan** sincronizado apos o build: falha o pipeline em CVEs `CRITICAL` ou `HIGH` (ignora unfixed)
- **Rollback automatico** via `kubectl rollout undo` caso o `rollout status` falhe no timeout de 300s

O workflow `infra-deploy.yaml` possui bloco `concurrency` (`infra-deploy-${{ github.ref }}`, `cancel-in-progress: false`) que evita execucoes simultaneas do mesmo ref.

### Via manual

> **IMPORTANTE:** Os repositorios ECR agora estao configurados com `image_tag_mutability = IMMUTABLE`.
> Nao e possivel sobrescrever uma tag existente. Use SEMPRE tags versionadas (ex: `v1.0.0`) no push manual.

```bash
# Login no ECR
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin \
  <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com

# Build e push de cada serviço (usar tag versionada, NUNCA reaproveitar a mesma tag)
VERSION="v1.0.0"
for svc in upload-service processing-service report-service; do
  docker build -t <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/archlens/${svc}:${VERSION} \
    services/${svc}/
  docker push <ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/archlens/${svc}:${VERSION}
done

# Aplicar deployments K8s (criar manifests ou usar kubectl set image)
kubectl set image deployment/upload-service \
  upload-service=<ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/archlens/upload-service:${VERSION} \
  -n archlens
```

---

## Etapa 7 — Configurar New Relic AWS API Polling

O IAM role `NewRelicInfrastructure-Integrations` foi criado no `01-foundation`.
Para ativá-lo:

1. Acesse **New Relic > Infrastructure > AWS**
2. Clique em **Add an AWS account**
3. Selecione **API Polling**
4. Informe o ARN do role: `newrelic_integration_role_arn` (output do 01-foundation)
5. Selecione os serviços: **RDS, S3, ALB, VPC, NAT Gateway**
6. Salve

---

## Etapa 8 — Validação final

```bash
# 1. Cluster saudável
kubectl get nodes -o wide
kubectl get pods -n archlens
kubectl get pods -n newrelic

# 2. Vault unsealed
kubectl exec vault-0 -n archlens -- vault status

# 3. RabbitMQ filas criadas
kubectl exec rabbitmq-0 -n archlens -- rabbitmqctl list_queues

# 4. Kong respondendo — autenticacao via JWT (mesmo metodo do docker-compose)
KONG_URL=$(kubectl get svc kong-gateway-proxy -n archlens \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Gerar JWT com o mesmo script usado no docker-compose
# (exporta KONG_JWT_SECRET com o mesmo valor guardado no Vault)
export KONG_JWT_SECRET=$(vault kv get -field=KONG_JWT_SECRET secret/archlens/kong)
JWT_TOKEN=$(python gateways/kong/generate-jwt.py)
curl -s http://${KONG_URL}/api/v1/analises -H "Authorization: Bearer ${JWT_TOKEN}"

# 5. HPA ativo e coletando métricas
kubectl get hpa -n archlens
# TARGETS deve mostrar valores reais (ex: 12%/70%), não <unknown>/70%

# 5.1 PodDisruptionBudgets garantindo resiliencia em SPOT reclaim
kubectl get pdb -n archlens
# Deve listar: upload-service-pdb, processing-service-pdb, report-service-pdb (ALLOWED DISRUPTIONS >= 1)

# 6. LiteLLM health
kubectl port-forward svc/litellm-proxy -n archlens 4000:4000 &
curl -s http://localhost:4000/health/liveliness

# 7. New Relic dados chegando
# Verificar em: New Relic > Infrastructure > Kubernetes
# Verificar em: New Relic > Infrastructure > Third-party services (PostgreSQL, RabbitMQ)
```

---

## Etapa 9 — Fluxo completo via GitHub Actions

Esta seção é uma **alternativa** às Etapas 1-6: em vez de rodar `terraform apply`
localmente, você dispara os workflows em `.github/workflows/` e deixa o pipeline
orquestrar a ordem `01 → 02 → 03 → k8s-manifests`.

**Os pré-requisitos continuam valendo:**
- Etapa 0 inteira (0.1-0.4) — workspaces CLI-driven criados, Variable Set com credenciais AWS, secrets no GitHub.
- Variáveis sensíveis de cada workspace (Etapas 1.1 / 2.1 / 3.1) já configuradas no TFC **antes** de disparar o workflow.

### 9.1 — Deploy inicial (first-time)

Na primeira subida há **3 paradas manuais obrigatórias** no meio do pipeline
(OIDC + Vault + Deployments). Por isso o `workflow_dispatch` é usado com
`workspace` específico a cada etapa, em vez de `workspace=all`.

**① Deploy do 01-foundation**

```
Actions > "Infra: Terraform Deploy" > Run workflow
  action: apply
  workspace: 01-foundation
```

O job `foundation-plan` roda primeiro e anexa o plano ao summary; o
`foundation-apply` aplica usando o `tfplan` artifact. Aguarde completar.

**② Deploy do 02-cluster**

```
Actions > "Infra: Terraform Deploy" > Run workflow
  action: apply
  workspace: 02-cluster
```

Após completar (~10-15 min por causa do EKS), configure `kubectl` local
conforme a Etapa 2.3 — isso **não** acontece no workflow porque as
credenciais ficam no seu kubeconfig local.

**③ Corrigir OIDC e re-aplicar 01-foundation (Etapa 2.4)**

Este passo **não pode** ser feito pelo workflow: você precisa obter o OIDC
issuer (`aws eks describe-cluster ...`), editar `infra/terraform/01-foundation/main.tf`
e commitar no branch. Depois:

```
Actions > "Infra: Terraform Deploy" > Run workflow
  action: apply
  workspace: 01-foundation
```

O plan vai mostrar mudança apenas nas trust policies dos IRSA roles.

**④ Deploy do 03-platform**

```
Actions > "Infra: Terraform Deploy" > Run workflow
  action: apply
  workspace: 03-platform
```

Ao final deste run, o job `k8s-manifests` roda automaticamente e aplica
`infra/k8s/ingress/kong-config.yaml` + `infra/k8s/hpa/` (veja o step
`Apply Kong manifests` e `Apply HPA manifests` em `infra-deploy.yaml`).

**⑤ Bootstrap do Vault (Etapas 4.1-4.6)**

Manual e **offline do pipeline** — init/unseal do Vault, popular secrets,
configurar Kubernetes Auth. Não automatize isso: as unseal keys e root
token nunca podem passar pelo runner do GitHub.

**⑥ Aplicar Deployments dos services (Etapa 5.0)**

Este passo não está no `infra-deploy.yaml` — os Deployments usam imagem
`PLACEHOLDER` que é substituída pelo workflow de services. Rode uma vez
localmente:

```bash
kubectl apply -f infra/k8s/deployments/
```

> **Por que não automatizar isso?** Se o job aplicasse os Deployments sem
> imagem válida, os pods ficariam em `ErrImagePull` e o `k8s-manifests`
> falharia na verificação. Melhor deixar explícito que o primeiro
> `kubectl set image` (⑦) é o que cria a imagem real.

**⑦ Deploy dos services (build + push + rollout)**

Tag de release dispara tudo:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Ou `workflow_dispatch`:

```
Actions > "Services: Build & Deploy" > Run workflow
  service: all
```

O workflow faz build com cache (`--cache-from`), scan Trivy (falha em
CVEs `CRITICAL`/`HIGH` com fix disponível), `kubectl set image` e
`rollout status` com rollback automático em caso de falha no timeout
de 300s (ver `services-deploy.yaml:166-173`).

**⑧ New Relic + validação final**

Etapa 7 (NR API polling) é feita via UI do New Relic. Etapa 8 (validação)
é manual via `kubectl` / `curl`.

### 9.2 — Deploys subsequentes (infra já estável)

Depois do first-time, uma mudança em `infra/terraform/**` segue o caminho simples:

```bash
# Opção A — por tag (dispara apply em workspace=all via `push: tags: infra/v*`)
git tag infra/v1.1.0
git push origin infra/v1.1.0
# ⚠ Atenção: a trigger por tag só roda os jobs *-plan (action != 'destroy'
# não mapeia para 'apply'). Para rodar apply é preciso usar workflow_dispatch.

# Opção B — workflow_dispatch (recomendado para apply)
Actions > "Infra: Terraform Deploy" > Run workflow
  action: apply
  workspace: all
```

Com `workspace=all`, a cadeia `foundation → cluster → platform → k8s-manifests`
roda na ordem correta por causa das dependências `needs:` entre os jobs. Em
deploy incremental isso é seguro porque OIDC, Vault e Deployments já existem.

Deploy de services continua via tag `v*` ou `workflow_dispatch` no
`services-deploy.yaml` — o job `detect-changes` + `matrix` permite deployar
só o service alterado.

### 9.3 — Destroy via GitHub Actions

```
Actions > "Infra: Terraform Deploy" > Run workflow
  action: destroy
  workspace: all
```

A cadeia de dependências (`platform-destroy` → `cluster-destroy` → `foundation-destroy`)
garante que os recursos sejam derrubados na ordem correta, evitando que a VPC
seja removida enquanto ainda há ENIs/SGs/LoadBalancers vinculados. Veja o bloco
`Ordem de destruição` abaixo para os `terraform destroy` equivalentes via CLI.

---

## Ordem de destruição (inversa)

Para destruir a infraestrutura, execute na ordem inversa:

```bash
# 1. Remover manifests K8s
kubectl delete -f infra/k8s/hpa/
kubectl delete -f infra/k8s/ingress/kong-config.yaml

# 2. Destruir 03-platform
cd infra/terraform/03-platform && terraform destroy

# 3. Destruir 02-cluster
cd infra/terraform/02-cluster && terraform destroy

# 4. Destruir 01-foundation
cd infra/terraform/01-foundation && terraform destroy
```

Ou via GitHub Actions: selecione `action: destroy` e `workspace: all`. A cadeia de dependencias do workflow ja roda na ordem correta (`platform-destroy` -> `cluster-destroy` -> `foundation-destroy`), evitando que VPC/subnets sejam removidas antes dos recursos que dependem delas (ENIs, SGs, LoadBalancers).

---

## Resumo dos secrets necessários

| Secret | Onde configurar | Usado por |
|--------|----------------|-----------|
| `db_password` | TF Cloud (foundation + platform) | RDS, nri-postgresql |
| `newrelic_account_id` | TF Cloud (foundation) | IAM trust policy NR |
| `newrelic_license_key` | TF Cloud (platform) | nri-bundle |
| `rabbitmq_password` | TF Cloud (platform) | RabbitMQ, nri-rabbitmq |
| `rabbitmq_erlang_cookie` | TF Cloud (platform) | RabbitMQ cluster |
| `GEMINI_API_KEY` | Vault | LiteLLM (Gemini 3.1 Flash Lite + 2.5 Flash fallback) |
| `LITELLM_MASTER_KEY` | Vault | LiteLLM |
| `litellm_db_password` | TF Cloud (platform) | Bootstrap Job `litellm-db-bootstrap` + `LITELLM_DATABASE_URL` |
| `KONG_JWT_SECRET` | Vault | Kong Ingress (Secret `archlens-jwt-credential`) + `generate-jwt.py` |
| `TF_API_TOKEN` | GitHub Secrets | CI/CD workflows |
| `AWS_ACCESS_KEY_ID` | TF Cloud Variable Set | Todos os workspaces |
| `AWS_SECRET_ACCESS_KEY` | TF Cloud Variable Set | Todos os workspaces |
