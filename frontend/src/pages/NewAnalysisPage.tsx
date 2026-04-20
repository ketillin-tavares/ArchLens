import { useState } from "react";
import { TOKENS } from "@/config/tokens";
import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import { FileDrop } from "@/components/analysis/FileDrop";
import { uploadDiagrama } from "@/services/analysisService";
import { ApiError, UnauthorizedError } from "@/services/httpClient";

const MAX_BYTES = 10 * 1024 * 1024;
const ACCEPTED_MIME = ["image/png", "image/jpeg", "application/pdf"] as const;
const ACCEPTED_EXT = ["png", "jpg", "jpeg", "pdf"] as const;

interface NewAnalysisPageProps {
  onStarted: (analiseId: string, titulo: string) => void;
  onCancel?: () => void;
}

export function NewAnalysisPage({
  onStarted,
  onCancel,
}: NewAnalysisPageProps): JSX.Element {
  const [file, setFile] = useState<File | null>(null);
  const [titulo, setTitulo] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const acceptFile = (next: File | null): void => {
    setError("");
    if (!next) {
      setFile(null);
      return;
    }
    const ext = (next.name.split(".").pop() ?? "").toLowerCase();
    const okType =
      (ACCEPTED_MIME as readonly string[]).includes(next.type) ||
      (ACCEPTED_EXT as readonly string[]).includes(ext);
    if (!okType) {
      setError("Formato não suportado. Use PNG, JPG, JPEG ou PDF.");
      return;
    }
    if (next.size > MAX_BYTES) {
      setError(
        `Arquivo muito grande. Máximo 10 MB (enviado: ${(
          next.size /
          1024 /
          1024
        ).toFixed(1)} MB).`,
      );
      return;
    }
    setFile(next);
  };

  const submit = async (): Promise<void> => {
    if (!file) return;
    setSubmitting(true);
    setError("");
    try {
      const response = await uploadDiagrama(file);
      onStarted(
        response.analise_id,
        titulo || "Análise Arquitetural - Diagrama de Microsserviços",
      );
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        setError("Sessão expirada. Faça login novamente.");
      } else if (err instanceof ApiError) {
        setError(`Falha no upload (HTTP ${err.status}): ${err.message}`);
      } else {
        setError("Erro inesperado ao enviar o diagrama.");
      }
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 880, margin: "0 auto", padding: "48px 28px 80px" }}>
      <div style={{ marginBottom: 28 }}>
        <div
          style={{
            fontFamily: "Geist Mono",
            fontSize: 11,
            color: TOKENS.slate,
            letterSpacing: 1.5,
            textTransform: "uppercase",
            marginBottom: 6,
          }}
        >
          Nova análise
        </div>
        <h1
          style={{
            fontFamily: "Geist",
            fontWeight: 600,
            fontSize: 32,
            color: TOKENS.navy,
            letterSpacing: -1,
            margin: "0 0 6px",
          }}
        >
          Envie seu diagrama
        </h1>
        <p
          style={{
            fontFamily: "Geist",
            fontSize: 15,
            color: TOKENS.slate2,
            margin: 0,
          }}
        >
          ArchLens identifica componentes, mapeia conexões e aponta os riscos
          arquiteturais do seu sistema.
        </p>
      </div>

      <div
        style={{
          border: `1px solid ${TOKENS.line}`,
          borderRadius: 12,
          background: "#fff",
          padding: 24,
          display: "flex",
          flexDirection: "column",
          gap: 20,
        }}
      >
        <TextField
          label="Título da análise"
          placeholder="Análise Arquitetural - Diagrama de Microsserviços"
          value={titulo}
          onChange={(event) => setTitulo(event.target.value)}
          hint="Opcional — usado para identificar o relatório depois."
        />

        <div>
          <div
            style={{
              fontSize: 13,
              fontWeight: 500,
              color: TOKENS.ink,
              marginBottom: 8,
            }}
          >
            Diagrama
          </div>
          <FileDrop file={file} onFile={acceptFile} error={error} />
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontFamily: "Geist Mono",
            fontSize: 11,
            color: TOKENS.slate,
          }}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.3"
          >
            <circle cx="7" cy="7" r="5.5" />
            <path d="M7 4.5V7m0 2.2v.1" />
          </svg>
          Formatos aceitos: PNG, JPG, JPEG, PDF · Máximo 10 MB
        </div>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-end",
          marginTop: 24,
          gap: 10,
        }}
      >
        <Button variant="ghost" onClick={onCancel}>
          Cancelar
        </Button>
        <Button
          variant="accent"
          disabled={!file || submitting}
          onClick={submit}
        >
          {submitting ? "Analisando…" : "Analisar diagrama"}
          {!submitting && (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path
                d="M3 7h8m0 0L7 3m4 4L7 11"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </Button>
      </div>
    </div>
  );
}
