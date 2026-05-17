import { useState } from "react";
import { TOKENS } from "@/config/tokens";
import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/ui/TextField";
import { getAnaliseStatus } from "@/services/analysisService";
import { ApiError, UnauthorizedError } from "@/services/httpClient";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

interface SearchReportPageProps {
  readonly onFound: (analiseId: string) => void;
}

export function SearchReportPage({
  onFound,
}: SearchReportPageProps): JSX.Element {
  const [uuid, setUuid] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (): Promise<void> => {
    const trimmed = uuid.trim();
    if (!UUID_PATTERN.test(trimmed)) {
      setError("UUID inválido. Use o formato 8-4-4-4-12 (ex: 550e8400-...).");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await getAnaliseStatus(trimmed);
      onFound(trimmed);
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        setError("Sessão expirada. Faça login novamente.");
      } else if (err instanceof ApiError) {
        if (err.status === 404) {
          setError("Nenhum relatório encontrado para este UUID.");
        } else {
          setError(`Falha na busca (HTTP ${err.status}): ${err.message}`);
        }
      } else {
        setError("Erro inesperado ao buscar o relatório.");
      }
      setSubmitting(false);
    }
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>): void => {
    if (event.key === "Enter" && !submitting) {
      void submit();
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
          Buscar relatório
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
          Localize uma análise por UUID
        </h1>
        <p
          style={{
            fontFamily: "Geist",
            fontSize: 15,
            color: TOKENS.slate2,
            margin: 0,
          }}
        >
          Cole o identificador da análise para abrir o relatório correspondente.
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
          label="UUID da análise"
          placeholder="550e8400-e29b-41d4-a716-446655440000"
          value={uuid}
          onChange={(event) => {
            setUuid(event.target.value);
            if (error) setError("");
          }}
          onKeyDown={onKeyDown}
          error={error || undefined}
          hint="Formato 8-4-4-4-12 (32 caracteres hexadecimais com hífens)."
          autoComplete="off"
          spellCheck={false}
          style={{ fontFamily: "Geist Mono" }}
        />

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
          O UUID é exibido após o envio de um diagrama e na URL do relatório.
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
        <Button
          variant="accent"
          disabled={!uuid.trim() || submitting}
          onClick={submit}
        >
          {submitting ? "Buscando…" : "Buscar relatório"}
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
