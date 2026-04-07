# ArchLens — New Relic Alerts

> Configuração completa de alertas para os três serviços.
>
> Todos os alertas usam **NRQL Alert Conditions** dentro de uma **Alert Policy**.

---

## 1. Como criar uma Alert Policy

### Via UI
1. Acesse **New Relic → Alerts → Alert Policies**
2. Clique em **+ New alert policy**
3. Nome sugerido: `ArchLens - Platform Alerts`
4. Issue creation preference: **One issue per condition and signal** (recomendado para microserviços)

### Via NerdGraph API (automatizado)
```graphql
mutation {
  alertsPolicyCreate(accountId: 7557083, policy: {
    incidentPreference: PER_CONDITION_AND_TARGET
    name: "ArchLens - Platform Alerts"
  }) {
    id
    name
  }
}
```

---

## 2. Alertas por Categoria

### 2.1 Taxa de Erro — Por Serviço

**Objetivo:** Alertar quando a taxa de erros HTTP/APM ultrapassa thresholds aceitáveis.

| Serviço | Warning | Critical | Janela |
|---|---|---|---|
| upload-service | > 2% | > 5% | 5 min |
| processing-service | > 2% | > 5% | 5 min |
| report-service | > 2% | > 5% | 5 min |

**NRQL — upload-service:**
```sql
SELECT percentage(count(*), WHERE error IS true)
FROM Transaction
WHERE appName = 'upload-service'
```

**NRQL — processing-service:**
```sql
SELECT percentage(count(*), WHERE error IS true)
FROM Transaction
WHERE appName = 'processing-service'
```

**NRQL — report-service:**
```sql
SELECT percentage(count(*), WHERE error IS true)
FROM Transaction
WHERE appName = 'report-service'
```

> Configurar como **Static threshold**, evaluation window: **5 minutes**, threshold: warning=2, critical=5.

---

### 2.2 Latência P95 — APM por Serviço

**Objetivo:** Detectar degradação de performance antes que o usuário perceba.

| Serviço | Warning (s) | Critical (s) | Janela |
|---|---|---|---|
| upload-service | > 2s | > 10s | 5 min |
| processing-service | > 60s | > 120s | 5 min |
| report-service | > 30s | > 60s | 5 min |

**NRQL — upload-service:**
```sql
SELECT percentile(duration, 95)
FROM Transaction
WHERE appName = 'upload-service'
```

**NRQL — processing-service:**
```sql
SELECT percentile(duration, 95)
FROM Transaction
WHERE appName = 'processing-service'
```

**NRQL — report-service:**
```sql
SELECT percentile(duration, 95)
FROM Transaction
WHERE appName = 'report-service'
```

---

### 2.3 Pipeline E2E — Tempo Total de Processamento

**Objetivo:** Alertar quando o ciclo completo (upload → relatório) demora mais que o esperado.

```sql
SELECT average(newrelic.timeslice.value)
FROM Metric
WHERE metricTimesliceName = 'Custom/Analise/TempoProcessamento'
```

| Threshold | Valor |
|---|---|
| Warning | > 120s |
| Critical | > 300s |
| Janela | 10 min |

---

### 2.4 Falhas no Pipeline

**Objetivo:** Qualquer falha no pipeline é um sinal crítico.

```sql
SELECT sum(newrelic.timeslice.value)
FROM Metric
WHERE metricTimesliceName = 'Custom/Analise/Falhas'
```

| Threshold | Valor |
|---|---|
| Warning | >= 1 falha |
| Critical | >= 5 falhas |
| Janela | 5 min |

---

### 2.5 Dead Letter Queues (DLQ) — Acúmulo de Mensagens

**Objetivo:** Mensagens em DLQ indicam falhas não tratadas no consumo — requer investigação imediata.

```sql
SELECT sum(queue.messagesReadyCount)
FROM RabbitmqQueueSample
WHERE queue.name LIKE '%.dlq' OR queue.name LIKE '%dead%'
```

| Threshold | Valor |
|---|---|
| Warning | >= 1 mensagem |
| Critical | >= 10 mensagens |
| Janela | 5 min |

> **Dica:** Criar uma condition por fila para isolar qual serviço está com problema:

```sql
-- processing-service DLQ
SELECT average(queue.messagesReadyCount)
FROM RabbitmqQueueSample
WHERE queue.name = 'processing-service.pipeline.dlq'

-- report-service DLQ
SELECT average(queue.messagesReadyCount)
FROM RabbitmqQueueSample
WHERE queue.name = 'report-service.reports.dlq'

-- upload-service DLQ
SELECT average(queue.messagesReadyCount)
FROM RabbitmqQueueSample
WHERE queue.name = 'upload-service.status-updates.dlq'
```

---

### 2.6 RabbitMQ — Profundidade das Filas Principais

**Objetivo:** Detectar backlog crescente antes que os consumidores estejam sobrecarregados.

```sql
SELECT average(queue.messagesReadyCount)
FROM RabbitmqQueueSample
WHERE queue.name = 'processing-service.pipeline'
```

| Threshold | Valor |
|---|---|
| Warning | > 50 mensagens |
| Critical | > 200 mensagens |
| Janela | 10 min |

> Replicar para `report-service.reports` e `upload-service.status-updates`.

---

### 2.7 AI Pipeline — Confiança Média dos Componentes

**Objetivo:** Detectar degradação na qualidade das análises da IA.

```sql
SELECT average(newrelic.timeslice.value)
FROM Metric
WHERE metricTimesliceName = 'Custom/AI/AvgConfidence'
```

| Threshold | Valor | Direção |
|---|---|---|
| Warning | < 0.75 | Abaixo do threshold |
| Critical | < 0.60 | Abaixo do threshold |
| Janela | 15 min |  |

> **Atenção:** Configurar como threshold **below** (abaixo). A confiança deve ficar acima de 0.75.

---

### 2.8 AI Pipeline — Retentativas de Validação Excessivas

**Objetivo:** Retentativas altas indicam que a IA está produzindo outputs inválidos com frequência.

```sql
SELECT sum(newrelic.timeslice.value)
FROM Metric
WHERE metricTimesliceName = 'Custom/AI/ValidationRetries'
```

| Threshold | Valor |
|---|---|
| Warning | > 10 |
| Critical | > 30 |
| Janela | 10 min |

---

### 2.9 AI Pipeline — Taxa de Falhas (Evento AnaliseFalha)

**Objetivo:** Monitorar falhas diretas no pipeline de IA via custom events.

```sql
SELECT count(*)
FROM AnaliseFalha
```

| Threshold | Valor |
|---|---|
| Warning | > 2 por janela |
| Critical | > 5 por janela |
| Janela | 5 min |

> **Dica extra:** Criar alert separado por tipo de erro:

```sql
SELECT count(*)
FROM AnaliseFalha
WHERE tipo_erro = 'TimeoutError'
```

---

### 2.10 Infraestrutura — CPU dos Containers

**Objetivo:** Detectar containers com CPU alta antes de impactar a performance.

```sql
SELECT average(cpuPercent)
FROM ContainerSample
WHERE containerName IN ('upload-service', 'processing-service', 'report-service')
FACET containerName
```

| Threshold | Valor |
|---|---|
| Warning | > 70% |
| Critical | > 85% |
| Janela | 5 min |

> Usar **FACET** para criar alertas individuais por container (New Relic cria signals separados automaticamente).

---

### 2.11 Infraestrutura — Memória dos Containers

**Objetivo:** Detectar memory leak ou containers com pouca memória disponível.

```sql
SELECT average(memoryUsageBytes) / average(memoryLimitBytes) * 100
FROM ContainerSample
WHERE containerName IN ('upload-service', 'processing-service', 'report-service')
FACET containerName
```

| Threshold | Valor |
|---|---|
| Warning | > 75% |
| Critical | > 90% |
| Janela | 5 min |

---

### 2.12 Logs — Volume de Logs de Erro

**Objetivo:** Detectar bursts de erros nos logs antes de impactar o APM.

```sql
SELECT count(*)
FROM Log
WHERE level = 'ERROR'
  AND service.name IN ('upload-service', 'processing-service', 'report-service')
FACET service.name
```

| Threshold | Valor |
|---|---|
| Warning | > 10 por 5 min |
| Critical | > 50 por 5 min |
| Janela | 5 min |

---

### 2.13 Apdex — Experiência do Usuário Final

**Objetivo:** Monitorar a experiência percebida no upload-service (endpoint principal do usuário).

```sql
SELECT apdex(duration, 0.5)
FROM Transaction
WHERE appName = 'upload-service'
```

| Threshold | Valor | Direção |
|---|---|---|
| Warning | < 0.85 | Abaixo |
| Critical | < 0.70 | Abaixo |
| Janela | 10 min |  |

---

### 2.14 Relatório — Tempo de Geração

**Objetivo:** O LiteLLM pode ter latência variável — alertar antes do timeout.

```sql
SELECT average(newrelic.timeslice.value)
FROM Metric
WHERE metricTimesliceName = 'Custom/Relatorio/TempoGeracao'
```

| Threshold | Valor |
|---|---|
| Warning | > 30s |
| Critical | > 60s |
| Janela | 10 min |

---

### 2.15 PostgreSQL — Latência de Query

**Objetivo:** Detectar queries lentas que estão travando a aplicação.

```sql
SELECT average(databaseDuration)
FROM Transaction
WHERE appName IN ('upload-service', 'processing-service', 'report-service')
  AND databaseDuration IS NOT NULL
FACET appName
```

| Threshold | Valor |
|---|---|
| Warning | > 0.5s |
| Critical | > 2s |
| Janela | 5 min |

---

## 3. Configuração de Notificações

### Canais sugeridos

| Canal | Quando usar |
|---|---|
| **Email** | Warning — revisão não urgente |
| **Slack** | Warning + Critical — visibilidade da equipe |
| **PagerDuty / OpsGenie** | Critical — on-call |
| **Webhook** | Integrações customizadas (Jira, etc.) |

### Criar Destination no New Relic

1. Acesse **Alerts → Destinations**
2. Clique **+ Add destination**
3. Configure Slack, email ou webhook
4. Associe ao **Workflow** (ver abaixo)

### Criar Workflow

1. Acesse **Alerts → Workflows**
2. Clique **+ Add a workflow**
3. Configure:
   - **Filter:** selecione a policy `ArchLens - Platform Alerts`
   - **Notify:** escolha os destinos (Slack para warning, PagerDuty para critical)
   - **Enrichments (opcional):** adicione NRQL para enriquecer a notificação com contexto

**Exemplo de enrichment útil no Workflow:**
```sql
-- Adicionar últimos erros no alerta de taxa de erro
SELECT count(*), latest(errorMessage), latest(errorClass)
FROM TransactionError
WHERE appName IN ('upload-service', 'processing-service', 'report-service')
FACET appName
SINCE 5 minutes ago
LIMIT 5
```

---

## 4. Mute Rules — Reduzir Ruído

Crie **mute rules** para suprimir alertas durante:
- Deploy windows (ex: toda segunda às 02:00-03:00)
- Ambientes de staging quando testando falhas intencionais

```
Alerts → Muting Rules → + Add muting rule
Condição: tags.environment = 'staging'
Schedule: recorrente (ex: seg-sex 01:00-03:00)
```
