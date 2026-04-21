# ArchLens — Terraform CLI Reference

Este documento descreve como executar o provisionamento da infraestrutura ArchLens
**via Terraform CLI** (localmente ou em runners CI/CD). É complementar ao
[step-by-step.md](../infra/terraform/step-by-step.md), que documenta o fluxo
completo de primeiro deploy e o ciclo via GitHub Actions.

---

## 1. Preparação do Ambiente

### 1.1 Ferramentas necessárias

| Ferramenta | Versão mínima | Instalação |
|------------|---------------|------------|
| Terraform CLI | >= 1.5 | `brew install terraform` / [releases](https://developer.hashicorp.com/terraform/install) |
| AWS CLI v2 | >= 2.15 | `brew install awscli` / [docs](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| kubectl | >= 1.29 | `brew install kubectl` |
| vault CLI | >= 1.15 | `brew install vault` |

### 1.2 Configurar AWS CLI

```bash
aws configure
# AWS Access Key ID: <sua-access-key>
# AWS Secret Access Key: <sua-secret-key>
# Default region name: us-east-2
# Default output format: json
```

Verificar autenticação:

```bash
aws sts get-caller-identity
# Deve retornar Account, UserId e ARN sem erros
```

**Permissões IAM necessárias:** IAM, VPC, EKS, RDS, S3, ECR, ELB (ALB), EC2,
CloudFront, SSM, CloudWatch. Em ambiente de dev recomenda-se `AdministratorAccess`.
Em produção, use um role com escopo mínimo.

### 1.3 Autenticar no Terraform Cloud

Os 4 workspaces usam o Terraform Cloud como backend remoto (organização `archlens`).
A CLI precisa de um token para ler/escrever o state e disparar runs remotos:

```bash
terraform login
# Abre o browser para gerar um token de usuário
# O token é salvo em ~/.terraform.d/credentials.tfrc.json
```

Alternativamente, via variável de ambiente (útil em CI/CD):

```bash
export TF_TOKEN_app_terraform_io="<seu-token-tfc>"
```

---

## 2. Inicialização e Workspaces

### 2.1 Estrutura de workspaces

O projeto usa **4 workspaces CLI-driven** no Terraform Cloud, com execução obrigatoriamente
ordenada (cada workspace lê outputs do anterior via `terraform_remote_state`):

| Ordem | Workspace TFC | Diretório local |
|-------|---------------|-----------------|
| 1 | `archlens-foundation` | `infra/terraform/01-foundation` |
| 2 | `archlens-cluster` | `infra/terraform/02-cluster` |
| 3 | `archlens-platform` | `infra/terraform/03-platform` |
| 4 | `archlens-frontend` | `infra/terraform/04-frontend` |

> O workspace `04-frontend` é independente dos demais em termos de recursos
> (não usa EKS, VPC nem RDS), mas lê o output `kong_url` do workspace `03-platform`
> via `terraform_remote_state`. Aplique-o **após** o `03-platform` para que o CSP
> do CloudFront contenha a URL real do Kong.

### 2.2 Inicializar cada workspace

Execute `terraform init` dentro do diretório de cada workspace. O init:
- Baixa os providers declarados em `required_providers`
- Configura o backend remoto (Terraform Cloud)
- Baixa os módulos referenciados (AWS VPC, EKS, RDS)

```bash
# Exemplo para 01-foundation (repetir para os demais)
cd infra/terraform/01-foundation
terraform init

# Saída esperada:
# Terraform Cloud has been successfully initialized!
# Terraform has been successfully initialized!
```

> **Nota:** O `terraform init` não cria o workspace no TFC. Os workspaces devem
> ser criados manualmente na UI do Terraform Cloud antes do primeiro `init`.
> Consulte a Etapa 0 do [step-by-step.md](../infra/terraform/step-by-step.md).

### 2.3 Gerenciar ambientes via variáveis de workspace

Não há workspaces locais separados (como `terraform workspace new dev`). O isolamento
de ambiente (`dev` / `prod`) é feito por variáveis Terraform configuradas no TFC:

| Variável | dev | prod |
|----------|-----|------|
| `environment` | `dev` | `prod` |
| `node_capacity_type` | `SPOT` | `ON_DEMAND` |
| `vault_service_type` | `LoadBalancer` (bootstrap) → `ClusterIP` | `ClusterIP` |
| `rds_instance_class` | `db.t3.micro` | `db.t3.small` ou maior |

Para criar um ambiente de prod, crie 4 novos workspaces no TFC (ex:
`archlens-foundation-prod`) apontando para os mesmos diretórios com variáveis
de prod. Cada workspace mantém seu próprio state file isolado.

---

## 3. Plano e Aplicação

### 3.1 Fluxo padrão

Como os workspaces usam **Execution Mode: Remote**, o `terraform plan` e
`terraform apply` são executados nos runners do Terraform Cloud. A CLI local
apenas envia o código e exibe o output em streaming.

```bash
cd infra/terraform/01-foundation

# Ver o plano (executa remotamente, resultado exibido localmente)
terraform plan

# Salvar o plano em arquivo para apply determinístico
terraform plan -out=tfplan.bin

# Aplicar o plano salvo
terraform apply tfplan.bin

# Aplicar sem confirmação manual (usar com cautela)
terraform apply -auto-approve
```

> **Por que `-out`?** O arquivo `tfplan.bin` congela o plano no momento da geração.
> Um `terraform apply` sem arquivo re-executa o plan internamente — o que pode resultar
> em um apply diferente do plan que você revisou caso haja drift entre os dois
> instantes. Use `-out` + `apply <arquivo>` em pipelines e em mudanças de risco.

### 3.2 Passar variáveis pela CLI

Para substituir variáveis de workspace sem alterar o TFC (útil para testes locais):

```bash
# Passar uma variável individual
terraform plan -var="environment=staging"

# Passar múltiplas variáveis via arquivo
cat > override.tfvars <<EOF
environment       = "staging"
rds_instance_class = "db.t3.small"
EOF

terraform plan -var-file=override.tfvars
```

> **Atenção:** variáveis passadas via `-var` ou `-var-file` têm precedência sobre
> as variáveis configuradas no Terraform Cloud Variable Set.

### 3.3 Ver outputs após apply

```bash
# Todos os outputs
terraform output

# Output específico (sem sensitive masking)
terraform output -raw rds_address

# Output de 03-platform para obter URL do Kong
terraform -chdir=infra/terraform/03-platform output -raw kong_url
```

### 3.4 Sequência completa de apply

```bash
# 1. Foundation (VPC, RDS, S3, ECR, IAM)
cd infra/terraform/01-foundation && terraform init && terraform plan -out=tfplan.bin && terraform apply tfplan.bin

# 2. Cluster (EKS, OIDC, ALB Controller)
cd ../02-cluster && terraform init && terraform plan -out=tfplan.bin && terraform apply tfplan.bin

# 3. [MANUAL] Atualizar OIDC no 01-foundation — ver Seção 5.1

# 4. Platform (Vault, RabbitMQ, Kong, LiteLLM, New Relic)
cd ../03-platform && terraform init && terraform plan -out=tfplan.bin && terraform apply tfplan.bin

# 5. Frontend (S3, CloudFront, SSM)
cd ../04-frontend && terraform init && terraform plan -out=tfplan.bin && terraform apply tfplan.bin
```

---

## 4. Gestão de State

### 4.1 Backend remoto — Terraform Cloud

O state de todos os workspaces é armazenado no **Terraform Cloud** (não em S3/DynamoDB).
A configuração do backend está em cada `main.tf`:

```hcl
terraform {
  cloud {
    organization = "archlens"
    workspaces { name = "archlens-foundation" }
  }
}
```

O TFC oferece:
- **State locking automático** — impede runs concorrentes no mesmo workspace
- **Histórico de state** — rollback para qualquer versão anterior via UI
- **Criptografia em repouso** — AES-256 gerenciado pelo TFC
- **Auditoria** — log de quem executou cada run e quando

### 4.2 Inspecionar o state localmente

```bash
# Listar todos os recursos rastreados
terraform state list

# Inspecionar um recurso específico
terraform state show module.vpc.aws_vpc.this[0]

# Remover um recurso do state sem destruí-lo (use com cuidado)
terraform state rm aws_s3_bucket.diagramas
```

### 4.3 Importar recurso existente

Se um recurso foi criado manualmente na AWS e precisa ser gerenciado pelo Terraform:

```bash
# Exemplo: importar um bucket S3 existente
terraform import aws_s3_bucket.diagramas archlens-diagramas-abc123

# Após o import, execute plan para verificar drift
terraform plan
```

### 4.4 Refresh de state

Se o state local estiver dessincronizado com a AWS (ex: após mudança manual):

```bash
terraform refresh
# ou
terraform plan -refresh-only
```

### 4.5 Leitura de state entre workspaces

Os workspaces `02-cluster`, `03-platform` e `04-frontend` leem outputs de workspaces
anteriores via `terraform_remote_state`. Para que funcione, o workspace de origem
**precisa ter sido aplicado com sucesso** antes do plan do workspace seguinte.
Outputs sensíveis (`rds_address`, etc.) são acessíveis via remote state apenas
dentro da organização TFC `archlens`.

---

## 5. Procedimentos Operacionais

### 5.1 Atualizar OIDC após criar o cluster (obrigatório)

O placeholder `REPLACE_WITH_OIDC_ID` em `01-foundation/main.tf` deve ser substituído
pelo OIDC issuer real do EKS **após o apply do `02-cluster`**. Sem isso, os IRSA
roles de `upload-service-sa` e `processing-service-sa` apontam para um provider
inexistente e os pods falham ao assumir os roles IAM para acesso ao S3.

```bash
# 1. Obter o OIDC issuer ID
OIDC_ID=$(aws eks describe-cluster \
  --name archlens-cluster \
  --query "cluster.identity.oidc.issuer" \
  --output text | sed 's|https://||')
echo $OIDC_ID
# Saída: oidc.eks.us-east-2.amazonaws.com/id/ABCDEF1234567890

# 2. Atualizar o locals no main.tf do 01-foundation:
#    oidc_provider = "oidc.eks.us-east-2.amazonaws.com/id/ABCDEF1234567890"

# 3. Re-aplicar 01-foundation (only trust policies mudam)
cd infra/terraform/01-foundation
terraform plan   # deve mostrar update nos aws_iam_role resources
terraform apply
```

### 5.2 Alterar Vault de LoadBalancer para ClusterIP (pós-bootstrap)

```bash
# No TFC, altere a variável vault_service_type de "LoadBalancer" para "ClusterIP"
# e re-aplique o workspace 03-platform:
cd infra/terraform/03-platform
terraform plan   # mostra modificação no helm_release.vault (service.type)
terraform apply
```

### 5.3 Destruição (ordem inversa)

```bash
# 1. Remover manifests K8s antes de destruir o cluster
kubectl delete -f infra/k8s/hpa/
kubectl delete -f infra/k8s/ingress/kong-config.yaml

# 2. Destruir na ordem inversa
cd infra/terraform/03-platform && terraform destroy
cd ../02-cluster && terraform destroy
cd ../01-foundation && terraform destroy

# 04-frontend pode ser destruído independentemente
cd infra/terraform/04-frontend && terraform destroy
```

---
