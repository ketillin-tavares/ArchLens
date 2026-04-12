# New Relic — ArchLens Setup Guide

---

## Arquivos

| Arquivo | Descrição |
|---|---|
| `dashboard.json` | Dashboard completo com 6 páginas — importar via NerdGraph API |
| `alerts.md` | Guia completo de alertas com NRQL, thresholds e configuração |

---

## Como importar o Dashboard

> **Antes de importar:** substitua todos os `"accountIds": [0]` no `dashboard.json` pelo seu Account ID do New Relic.
> Você pode encontrar o Account ID em **New Relic → User menu → API keys** ou em **Administration → Access management**.
>
> Exemplo com `sed`:
> ```bash
> sed -i 's/"accountIds": \[0\]/"accountIds": [SEU_ACCOUNT_ID]/g' dashboard.json
> ```

### Opção A — NerdGraph API (recomendado)

1. Acesse [one.newrelic.com/nerdgraph-playground](https://one.newrelic.com/nerdgraph-playground)
2. Cole a mutation abaixo substituindo `<ACCOUNT_ID>` pelo seu Account ID:

```graphql
mutation CreateDashboard($dashboard: DashboardInput!) {
  dashboardCreate(accountId: <ACCOUNT_ID>, dashboard: $dashboard) {
    entityResult {
      guid
      name
    }
    errors {
      description
      type
    }
  }
}
```

**Variáveis:**
```json
{
  "dashboard": <conteúdo de dashboard.json>
}
```

3. Execute a mutation — o `guid` retornado é o ID do dashboard criado.

### Opção B — UI (Import JSON)

1. Acesse **New Relic → Dashboards**
2. Clique no menu `⋮` → **Import dashboard**
3. Cole o conteúdo de `dashboard.json`
4. Clique em **Import**

---

## Estrutura do Dashboard

| Página | Conteúdo |
|---|---|
| **Visão Geral** | Golden signals: throughput, error rate, latência E2E, análises por status, AI confidence |
| **Upload Service** | APM, status das análises, tamanho dos uploads, tempo E2E, top erros, **retry & download endpoints** |
| **Processing Service (AI)** | Latência pipeline, confiança, componentes/riscos, retentativas, eventos AnaliseSucesso/AnaliseFalha |
| **Report Service** | Relatórios gerados, tempo de geração, duplicados, consultas, erros |
| **Infraestrutura & Mensageria** | Containers CPU/mem/rede, RabbitMQ queues, DLQs, PostgreSQL |
| **Logs & Erros** | Log volume por serviço/nível (loguru → stdlib → NR agent), erros em tempo real, top exceções, spans com erro |
| **Distributed Tracing** | Duração de spans por serviço, traces com erro, operações DB/AMQP |

---

## Métricas Customizadas Monitoradas

### Upload Service
| Métrica | Tipo | Descrição |
|---|---|---|
| `Custom/Analise/Status/recebido` | Counter | Análises recebidas |
| `Custom/Analise/Status/em_processamento` | Counter | Análises em processamento |
| `Custom/Analise/Status/analisado` | Counter | Análises concluídas com sucesso |
| `Custom/Analise/Status/erro` | Counter | Análises com erro |
| `Custom/Upload/TamanhoBytes` | Gauge | Tamanho do diagrama enviado |
| `Custom/Analise/TempoProcessamento` | Timer | Tempo total E2E (upload → relatório) |
| `Custom/Analise/Falhas` | Counter | Falhas recebidas via evento AnaliseFalhou |

### Processing Service
| Métrica | Tipo | Descrição |
|---|---|---|
| `Custom/AI/LatencySeconds` | Timer | Duração do pipeline de IA |
| `Custom/AI/AvgConfidence` | Gauge | Confiança média dos componentes detectados |
| `Custom/AI/ComponentCount` | Gauge | Total de componentes identificados |
| `Custom/AI/RiskCount` | Gauge | Total de riscos identificados |
| `Custom/AI/ValidationRetries` | Counter | Número de correções necessárias na validação |

### Report Service
| Métrica | Tipo | Descrição |
|---|---|---|
| `Custom/Relatorio/Gerados` | Counter | Relatórios gerados com sucesso |
| `Custom/Relatorio/TempoGeracao` | Timer | Tempo de geração do relatório |
| `Custom/Relatorio/Duplicados` | Counter | Eventos de relatório duplicados ignorados |
| `Custom/Relatorio/Consultas` | Counter | Consultas ao endpoint GET /v1/relatorios |

### Custom Events (Processing Service)
| Evento | Atributos | Descrição |
|---|---|---|
| `AnaliseIniciada` | `analise_id` | Pipeline iniciado |
| `AnaliseSucesso` | `analise_id`, `duracao_segundos`, `total_componentes`, `total_riscos` | Pipeline concluído |
| `AnaliseFalha` | `analise_id`, `erro`, `tipo_erro` | Pipeline falhou |

---
