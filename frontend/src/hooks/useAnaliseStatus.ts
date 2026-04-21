import { useEffect, useState } from "react";
import { getAnaliseStatus } from "@/services/analysisService";
import { ApiError, UnauthorizedError } from "@/services/httpClient";
import type { AnaliseResponse } from "@/types/AnaliseResponse";
import type { AnaliseStatus } from "@/types/AnaliseStatus";

const POLL_INTERVAL_MS = 2_000;
const TERMINAL_STATUSES: readonly AnaliseStatus[] = ["analisado", "erro"];

interface UseAnaliseStatusResult {
  analise: AnaliseResponse | null;
  error: string | null;
}

export const useAnaliseStatus = (
  analiseId: string,
): UseAnaliseStatusResult => {
  const [analise, setAnalise] = useState<AnaliseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timeoutId: number | undefined;

    const poll = async (): Promise<void> => {
      try {
        const current = await getAnaliseStatus(analiseId);
        if (cancelled) return;
        setAnalise(current);
        if (!TERMINAL_STATUSES.includes(current.status)) {
          timeoutId = window.setTimeout(poll, POLL_INTERVAL_MS);
        }
      } catch (err) {
        if (cancelled) return;
        if (err instanceof UnauthorizedError) {
          setError("Sessão expirada. Faça login novamente.");
        } else if (err instanceof ApiError) {
          setError(`Falha ao consultar análise (HTTP ${err.status}).`);
        } else {
          setError("Erro inesperado ao consultar a análise.");
        }
      }
    };

    void poll();

    return () => {
      cancelled = true;
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };
  }, [analiseId]);

  return { analise, error };
};
