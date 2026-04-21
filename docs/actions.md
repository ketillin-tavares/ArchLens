# GitHub Actions — Deploy Pipelines

Documentação dos workflows de CI/CD do ArchLens. Todos os arquivos estão em [`.github/workflows/`](../.github/workflows/).

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Pré-requisitos Externos ao Pipeline](#2-pré-requisitos-externos-ao-pipeline)
3. [Workflows Detalhados](#3-workflows-detalhados)
   - [services-deploy](#31-services-deploy)
   - [frontend-deploy](#32-frontend-deploy)
   - [infra-deploy](#33-infra-deploy)
   - [sonarcloud](#34-sonarcloud)
4. [Gestão de Secrets e Variables](#4-gestão-de-secrets-e-variables)
5. [Validação de Configuração](#5-validação-de-configuração)

---

## 1. Visão Geral

O projeto possui quatro workflows independentes. Cada um é disparado por um padrão de tag distinto (ou manualmente via `workflow_dispatch`), sem sobreposição:

| Workflow | Arquivo | Trigger (tag) | Trigger (push de branch) |
|---|---|---|---|
| Services Deploy | `services-deploy.yaml` | `v*` | — |
| Frontend Deploy | `frontend-deploy.yaml` | `fe-v*` | — |
| Infra Deploy | `infra-deploy.yaml` | `infra/v*` | — |
| SonarCloud Scan | `sonarcloud.yaml` | — | `main` |

**Ordem recomendada para um ambiente do zero:**

```
1. infra-deploy (apply) → Provisiona VPC, EKS, ECR, S3, CloudFront, SSM params
2. services-deploy      → Build e push das imagens para ECR + rollout no EKS
3. frontend-deploy      → Build do React + sync S3 + invalidação CloudFront
4. sonarcloud           → Análise de qualidade (automático após merge na main)
```

---

## 2. Pré-requisitos Externos ao Pipeline

Antes de executar qualquer workflow, os seguintes recursos precisam existir fora do GitHub Actions:

### 2.1 AWS

- **IAM User ou Role** com as permissões mínimas:
  - `ecr:*` (push de imagens)
  - `eks:DescribeCluster`, `eks:UpdateCluster`
  - `s3:*` (sync do frontend)
  - `cloudfront:CreateInvalidation`, `cloudfront:GetDistribution`, `cloudfront:ListDistributions`
  - `ssm:GetParameter` (leitura dos parâmetros de configuração do frontend)
- As credenciais desse usuário/role devem estar cadastradas nos Secrets do repositório como `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY`.

### 2.2 Terraform Cloud (HCP Terraform)

- Organização `archlens` criada no Terraform Cloud.
- Três workspaces configurados com backend remoto:
  - `archlens-01-foundation`
  - `archlens-02-cluster`
  - `archlens-03-platform`
- Um **API Token** do Terraform Cloud cadastrado no Secret `TF_API_TOKEN`.

### 2.3 SSM Parameter Store (populado pelo Terraform)

O workflow `frontend-deploy` **não usa** variáveis de build do GitHub. Toda a configuração de build-time vem do AWS SSM Parameter Store, populado automaticamente pelo workspace `03-platform` do Terraform. Os parâmetros necessários são:

| Parâmetro SSM | Descrição |
|---|---|
| `/archlens/frontend/<env>/api_gateway_url` | URL pública do Kong Gateway |
| `/archlens/frontend/<env>/clerk_publishable_key` | Chave pública do Clerk (autenticação) |
| `/archlens/frontend/<env>/cloudfront_distribution_id` | ID da distribuição CloudFront |

> `<env>` é `prod` ou `dev`, conforme o input do workflow.

### 2.4 SonarCloud

- Organização criada no [sonarcloud.io](https://sonarcloud.io).
- Quatro projetos configurados:
  - `<SONAR_ORGANIZATION>_archlens-upload-service`
  - `<SONAR_ORGANIZATION>_archlens-processing-service`
  - `<SONAR_ORGANIZATION>_archlens-report-service`
  - `<SONAR_ORGANIZATION>_archlens-frontend`
- O token de análise cadastrado no Secret `SONAR_TOKEN`.
- O ID da organização cadastrado na Variable `SONAR_ORGANIZATION`.

### 2.5 Amazon ECR

- Três repositórios ECR criados (provisionados pelo Terraform `01-foundation`):
  - `archlens/upload-service`
  - `archlens/processing-service`
  - `archlens/report-service`

---

## 3. Workflows Detalhados

### 3.1 Services Deploy

**Arquivo:** [`services-deploy.yaml`](../.github/workflows/services-deploy.yaml)

**Trigger:**
- Push de tag com padrão `v*` → deploya **todos** os serviços.
- `workflow_dispatch` → escolha do serviço (`all`, `upload-service`, `processing-service`, `report-service`).

**Como criar uma release:**
```bash
git tag v1.2.0
git push origin v1.2.0
```

**Stages:**

```
detect-changes
    └── build-deploy (matrix: upload | processing | report)
            ├── Build & push Docker image → ECR (tag: <tag-name> e latest)
            ├── Scan de vulnerabilidades (Trivy — bloqueia CRITICAL e HIGH)
            ├── kubectl set image → EKS
            └── kubectl rollout status (timeout 300s) → rollback automático se falhar
```

**Comportamento de rollback:** se `kubectl rollout status` não completar em 300s, o workflow executa automaticamente `kubectl rollout undo` e sai com erro.

**Secrets necessários:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

---

### 3.2 Frontend Deploy

**Arquivo:** [`frontend-deploy.yaml`](../.github/workflows/frontend-deploy.yaml)

**Trigger:**
- Push de tag com padrão `fe-v*` → deploya para `prod`.
- `workflow_dispatch` → escolha do ambiente (`prod` ou `dev`).

**Como criar uma release:**
```bash
git tag fe-v2.1.0
git push origin fe-v2.1.0
```

**Stages:**

```
build-deploy
    ├── Configure AWS Credentials
    ├── Fetch config do SSM (/archlens/frontend/<env>/)
    │       → VITE_KONG_BASE_URL, VITE_CLERK_PUBLISHABLE_KEY, S3_BUCKET
    ├── Resolve CloudFront Distribution ID (via SSM)
    ├── Setup Node 24 + npm ci
    ├── tsc --noEmit (typecheck)
    ├── npm run build
    ├── aws s3 sync (assets estáticos — cache-control: immutable, 1 ano)
    ├── aws s3 cp index.html (cache-control: no-store)
    ├── CloudFront Invalidation (/index.html e /)
    └── Wait invalidation completed (timeout: 10min)
```

**Concorrência:** dois deploys do mesmo ambiente não executam em paralelo (`cancel-in-progress: false`). O segundo aguarda o primeiro terminar.

**Secrets necessários:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

---

### 3.3 Infra Deploy

**Arquivo:** [`infra-deploy.yaml`](../.github/workflows/infra-deploy.yaml)

**Trigger:**
- Push de tag com padrão `infra/v*` → executa `plan` em todos os workspaces + aplica manifests K8s.
- `workflow_dispatch` → escolha de `action` (plan/apply/destroy), `workspace` e `environment`.

**Como criar uma release:**
```bash
git tag infra/v1.0.0
git push origin infra/v1.0.0
```

**Stages e dependências:**

```
Plan (todos os workspaces, em sequência):
  foundation-plan → cluster-plan → platform-plan

Apply (requer action=apply, em sequência):
  foundation-apply → cluster-apply → platform-apply → k8s-manifests

Destroy (requer action=destroy, ordem inversa):
  platform-destroy → cluster-destroy → foundation-destroy
```

> **Atenção — comportamento no push de tag:** na trigger por tag (`infra/v*`), os jobs de `-apply` são ignorados (requerem `action=apply`), mas o job `k8s-manifests` **é executado** mesmo assim, pois aceita `platform-apply.result == 'skipped'`. Isso significa que um push de tag `infra/v*` sempre aplica os manifests K8s (Kong Ingress + HPA), mesmo sem rodar o Terraform apply.

**Seleção de workspace no `workflow_dispatch`:**

| Workspace | O que provisiona |
|---|---|
| `01-foundation` | VPC, subnets, ECR, S3, IAM roles base |
| `02-cluster` | EKS cluster, node groups |
| `03-platform` | Kong, cert-manager, namespaces, SSM params, CloudFront |
| `all` | Todos em sequência |

**Secrets necessários:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `TF_API_TOKEN`

---

### 3.4 SonarCloud

**Arquivo:** [`sonarcloud.yaml`](../.github/workflows/sonarcloud.yaml)

**Trigger:**
- Push na branch `main` → escaneia apenas os serviços com arquivos alterados no commit (via `dorny/paths-filter`).
- `workflow_dispatch` → escaneia o serviço/componente escolhido independente de diff.

**Stages (serviços Python):**

```
detect-changes
    └── sonar-scan (matrix: upload | processing | report)
            ├── Setup Python 3.13 + uv
            ├── uv sync (instala deps + dev)
            ├── pytest --cov=src --cov-report=xml
            └── SonarCloud Scan (com cobertura XML)
```

**Stages (frontend):**

```
detect-changes
    └── sonar-scan-frontend
            ├── Setup Node 24 + npm ci
            └── SonarCloud Scan (apenas análise estática — sem cobertura de testes)
```

**Secrets necessários:** `SONAR_TOKEN`

**Variables necessárias:** `SONAR_ORGANIZATION`

---

## 4. Gestão de Secrets e Variables

Configure em: **GitHub → Repositório → Settings → Secrets and variables → Actions**

### 4.1 Repository Secrets

| Secret | Usado em | Descrição |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | services-deploy, frontend-deploy, infra-deploy | ID da chave de acesso IAM da AWS |
| `AWS_SECRET_ACCESS_KEY` | services-deploy, frontend-deploy, infra-deploy | Chave secreta IAM da AWS |
| `TF_API_TOKEN` | infra-deploy | Token de API do Terraform Cloud (HCP Terraform) para autenticação no backend remoto |
| `SONAR_TOKEN` | sonarcloud | Token de análise do SonarCloud (gerado em sonarcloud.io → Account → Security) |

### 4.2 Repository Variables

| Variable | Usado em | Descrição | Exemplo |
|---|---|---|---|
| `SONAR_ORGANIZATION` | sonarcloud | ID/slug da organização no SonarCloud | `minha-empresa` |

### 4.3 Parâmetros SSM (não são GitHub Secrets)

Esses parâmetros são populados automaticamente pelo Terraform (`03-platform`) e lidos diretamente pelo workflow via `aws ssm get-parameter`. Não precisam ser cadastrados no GitHub.

| Parâmetro | Tipo SSM | Descrição |
|---|---|---|
| `/archlens/frontend/prod/api_gateway_url` | String | URL pública do Kong Gateway (prod) |
| `/archlens/frontend/prod/clerk_publishable_key` | SecureString | Chave pública Clerk (prod) |
| `/archlens/frontend/prod/cloudfront_distribution_id` | String | ID da distribuição CloudFront (prod) |
| `/archlens/frontend/dev/api_gateway_url` | String | URL pública do Kong Gateway (dev) |
| `/archlens/frontend/dev/clerk_publishable_key` | SecureString | Chave pública Clerk (dev) |
| `/archlens/frontend/dev/cloudfront_distribution_id` | String | ID da distribuição CloudFront (dev) |

---
