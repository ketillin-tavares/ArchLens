import { useEffect, useState } from "react";
import { TOKENS } from "@/config/tokens";
import { Button } from "@/components/ui/Button";
import { Pill } from "@/components/ui/Pill";
import { ComponentBreakdown } from "@/components/analysis/ComponentBreakdown";
import { MarkdownRenderer } from "@/components/analysis/MarkdownRenderer";
import { MarkdownStyles } from "@/components/analysis/MarkdownStyles";
import { ScoreCard } from "@/components/analysis/ScoreCard";
import { SeverityCard } from "@/components/analysis/SeverityCard";
import { SkeletonReport } from "@/components/analysis/SkeletonReport";
import { useAnaliseStatus } from "@/hooks/useAnaliseStatus";
import {
  fetchMarkdown,
  getRelatorio,
  getRelatorioDownload,
} from "@/services/analysisService";
import { ApiError, UnauthorizedError } from "@/services/httpClient";
import type { AnalysisResult } from "@/types/AnalysisResult";
import type { DownloadResponse } from "@/types/DownloadResponse";
import {
  componentesPorTipo,
  componentsSub,
  formatDate,
  riskTone,
  totalRisksSub,
} from "./helpers/formatReport";

interface ResultsPageProps {
  analiseId: string;
  onNew: () => void;
}

const STATUS_LABEL: Record<string, string> = {
  recebido: "Na fila",
  processando: "Processando",
  analisado: "Concluído",
  erro: "Erro",
};

export function ResultsPage({
  analiseId,
  onNew,
}: ResultsPageProps): JSX.Element {
  const { analise, error: statusError } = useAnaliseStatus(analiseId);
  const [relatorio, setRelatorio] = useState<AnalysisResult | null>(null);
  const [download, setDownload] = useState<DownloadResponse | null>(null);
  const [markdown, setMarkdown] = useState("");
  const [loadingMd, setLoadingMd] = useState(true);
  const [reportError, setReportError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const ready = analise?.status === "analisado";
  const failed = analise?.status === "erro";
  const processing = !ready && !failed;
  const fetchError = statusError ?? reportError;

  useEffect(() => {
    if (!ready) return;
    let cancelled = false;
    setReportError(null);
    setLoadingMd(true);

    const load = async (): Promise<void> => {
      try {
        const [report, dl] = await Promise.all([
          getRelatorio(analiseId),
          getRelatorioDownload(analiseId),
        ]);
        if (cancelled) return;
        setRelatorio(report);
        setDownload(dl);
        const md = await fetchMarkdown(dl.download_url);
        if (cancelled) return;
        setMarkdown(md);
        setLoadingMd(false);
      } catch (err) {
        if (cancelled) return;
        setLoadingMd(false);
        if (err instanceof UnauthorizedError) {
          setReportError("Sessão expirada. Faça login novamente.");
        } else if (err instanceof ApiError) {
          setReportError(`Falha ao carregar relatório (HTTP ${err.status}).`);
        } else {
          setReportError("Erro ao carregar o conteúdo do relatório.");
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [analiseId, ready]);

  const downloadMd = (): void => {
    if (!markdown) return;
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `relatorio-${relatorio?.id ?? analiseId}.md`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const copyUrl = async (): Promise<void> => {
    if (!download?.download_url) return;
    try {
      await navigator.clipboard.writeText(download.download_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable — silently ignore */
    }
  };

  const estatisticas = relatorio?.conteudo?.estatisticas;
  const sev = estatisticas?.riscos_por_severidade;
  const tiposMap = componentesPorTipo(relatorio?.conteudo?.componentes);
  const pillTone = failed || fetchError ? "bad" : ready ? "good" : "blue";
  const pillLabel = fetchError
    ? "Erro"
    : STATUS_LABEL[analise?.status ?? ""] ?? "Carregando…";
  const headline = failed
    ? "Análise falhou"
    : processing
      ? "Analisando diagrama…"
      : (relatorio?.titulo ?? "Carregando…");

  return (
    <div
      style={{ maxWidth: 1080, margin: "0 auto", padding: "40px 28px 80px" }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 20,
          marginBottom: 28,
        }}
      >
        <div style={{ minWidth: 0, flex: 1 }}>
          <div
            style={{
              fontFamily: "Geist Mono",
              fontSize: 11,
              color: TOKENS.slate,
              letterSpacing: 1.5,
              textTransform: "uppercase",
              marginBottom: 8,
              display: "flex",
              alignItems: "center",
              gap: 10,
              flexWrap: "wrap",
            }}
          >
            <Pill tone={pillTone}>{pillLabel}</Pill>
            <span>
              análise · {analiseId.slice(0, 8)}
            </span>
            {relatorio && <span>· {formatDate(relatorio.criado_em)}</span>}
          </div>
          <h1
            style={{
              fontFamily: "Geist",
              fontWeight: 600,
              fontSize: 30,
              color: TOKENS.navy,
              letterSpacing: -1,
              margin: "0 0 6px",
              lineHeight: 1.2,
            }}
          >
            {headline}
          </h1>
          {relatorio && (
            <p
              style={{
                fontFamily: "Geist",
                fontSize: 15,
                color: TOKENS.slate2,
                margin: 0,
                lineHeight: 1.5,
                maxWidth: 760,
              }}
            >
              {relatorio.resumo}
            </p>
          )}
          {failed && analise?.erro_detalhe && (
            <p
              style={{
                fontFamily: "Geist",
                fontSize: 14,
                color: TOKENS.bad,
                marginTop: 8,
              }}
            >
              {analise.erro_detalhe}
            </p>
          )}
          {fetchError && (
            <p
              style={{
                fontFamily: "Geist",
                fontSize: 14,
                color: TOKENS.bad,
                marginTop: 8,
              }}
            >
              {fetchError}
            </p>
          )}
        </div>
        <div style={{ display: "flex", gap: 10, flexShrink: 0 }}>
          <Button
            variant="ghost"
            onClick={copyUrl}
            disabled={!download}
            icon={
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path d="M5 9l4-4m-3-2h3a2 2 0 012 2v3M4 7H3a2 2 0 00-2 2v1a2 2 0 002 2h4a2 2 0 002-2v-1" />
              </svg>
            }
          >
            {copied ? "Copiado!" : "Copiar link"}
          </Button>
          <Button
            variant="ghost"
            onClick={downloadMd}
            disabled={!markdown}
            icon={
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M7 2v8m0 0l-3-3m3 3l3-3M2 11v1h10v-1" />
              </svg>
            }
          >
            Download .md
          </Button>
          <Button variant="accent" onClick={onNew}>
            Nova análise
          </Button>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(6, 1fr)",
          gap: 12,
          marginBottom: 28,
        }}
      >
        <ScoreCard
          span={2}
          highlight
          value={estatisticas?.total_componentes ?? "—"}
          label="Componentes identificados"
          sub={componentsSub(tiposMap)}
        />
        <ScoreCard
          span={2}
          value={estatisticas?.total_riscos ?? "—"}
          label="Riscos detectados"
          sub={totalRisksSub(sev)}
          tone={riskTone(estatisticas?.total_riscos)}
        />
        <SeverityCard
          label="Crítica"
          value={sev?.critica ?? 0}
          tone="critica"
        />
        <SeverityCard label="Alta" value={sev?.alta ?? 0} tone="alta" />
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(6, 1fr)",
          gap: 12,
          marginBottom: 28,
        }}
      >
        <div style={{ gridColumn: "span 4" }}>
          <ComponentBreakdown
            types={relatorio ? tiposMap : undefined}
          />
        </div>
        <SeverityCard label="Média" value={sev?.media ?? 0} tone="media" />
        <SeverityCard label="Baixa" value={sev?.baixa ?? 0} tone="baixa" />
      </div>

      <div
        style={{
          border: `1px solid ${TOKENS.line}`,
          borderRadius: 14,
          background: "#fff",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 16,
            padding: "14px 24px",
            borderBottom: `1px solid ${TOKENS.line}`,
            background: TOKENS.mist,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              stroke={TOKENS.slate2}
              strokeWidth="1.3"
            >
              <path d="M3 2h7l3 3v9H3V2z" />
              <path d="M10 2v3h3" />
            </svg>
            <span
              style={{
                fontFamily: "Geist Mono",
                fontSize: 12,
                color: TOKENS.slate2,
              }}
            >
              relatorio.md
            </span>
          </div>
          {download && (
            <div
              style={{
                fontFamily: "Geist Mono",
                fontSize: 11,
                color: TOKENS.slate,
              }}
            >
              link expira em {Math.round(download.expires_in_seconds / 60)} min
            </div>
          )}
        </div>
        <div style={{ padding: "32px 56px 56px" }}>
          {loadingMd ? (
            <SkeletonReport />
          ) : (
            <div className="md-body">
              <MarkdownRenderer source={markdown} />
            </div>
          )}
        </div>
      </div>

      <MarkdownStyles />
    </div>
  );
}
