import type {
  RelatorioComponente,
  RiscosPorSeveridade,
} from "@/types/RelatorioConteudo";

export const componentesPorTipo = (
  componentes: RelatorioComponente[] | null | undefined,
): Record<string, number> => {
  if (!componentes) return {};
  return componentes.reduce<Record<string, number>>((acc, c) => {
    acc[c.tipo] = (acc[c.tipo] ?? 0) + 1;
    return acc;
  }, {});
};

export const componentsSub = (
  types: Record<string, number> | null | undefined,
): string => {
  if (!types) return "—";
  const entries = Object.entries(types);
  if (entries.length === 0) return "—";
  return entries
    .slice(0, 3)
    .map(([k, v]) => `${v} ${k}`)
    .join(" · ");
};

export const totalRisksSub = (
  sev: Partial<RiscosPorSeveridade> | null | undefined,
): string => {
  if (!sev) return "—";
  const critica = sev.critica ?? 0;
  const alta = sev.alta ?? 0;
  const media = sev.media ?? 0;
  const baixa = sev.baixa ?? 0;
  return `crít ${critica} · alta ${alta} · méd ${media} · baixa ${baixa}`;
};

export const riskTone = (
  total: number | null | undefined,
): "default" | "good" | "warn" | "bad" => {
  if (total == null) return "default";
  if (total >= 3) return "bad";
  if (total >= 1) return "warn";
  return "good";
};

export const formatDate = (iso: string | undefined, withTime = false): string => {
  if (!iso) return "—";
  const d = new Date(iso);
  const date = d.toLocaleDateString("pt-BR");
  if (!withTime) return date;
  const time = d.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });
  return `${date} ${time}`;
};
