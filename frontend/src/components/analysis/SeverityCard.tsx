import { TOKENS } from "@/config/tokens";
import type { RiskSeverity } from "@/types/RiskSeverity";

interface SeverityCardProps {
  label: string;
  value: number;
  tone: RiskSeverity;
}

const MAP: Record<RiskSeverity, { bg: string; fg: string; border: string }> = {
  critica: { bg: "#FEF2F2", fg: "#7F1D1D", border: "#FCA5A5" },
  alta: { bg: "#FEF2F2", fg: "#991B1B", border: "#FECACA" },
  media: { bg: "#FFFBEB", fg: "#92400E", border: "#FDE68A" },
  baixa: { bg: "#EFF6FF", fg: "#1E40AF", border: "#BFDBFE" },
};

export function SeverityCard({
  label,
  value,
  tone,
}: SeverityCardProps): JSX.Element {
  const map = MAP[tone];
  const active = value > 0;
  return (
    <div
      style={{
        background: active ? map.bg : "#fff",
        border: `1px solid ${active ? map.border : TOKENS.line}`,
        borderRadius: 12,
        padding: "14px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        minHeight: 108,
        justifyContent: "space-between",
      }}
    >
      <div
        style={{
          fontFamily: "Geist Mono",
          fontSize: 10,
          color: active ? map.fg : TOKENS.slate,
          letterSpacing: 1.5,
          textTransform: "uppercase",
        }}
      >
        Severidade · {label}
      </div>
      <div
        style={{
          fontFamily: "Geist",
          fontWeight: 600,
          fontSize: 32,
          letterSpacing: -1.2,
          lineHeight: 1,
          color: active ? map.fg : TOKENS.slate,
        }}
      >
        {value}
      </div>
    </div>
  );
}
