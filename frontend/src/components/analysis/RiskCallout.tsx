import type { RiskSeverity } from "@/types/RiskSeverity";

interface RiskCalloutProps {
  level: RiskSeverity;
  title: string;
  body: string;
}

const STYLES: Record<
  RiskSeverity,
  { bg: string; border: string; color: string; tag: string }
> = {
  critica: {
    bg: "#FEF2F2",
    border: "#FCA5A5",
    color: "#7F1D1D",
    tag: "CRÍTICO",
  },
  alta: { bg: "#FEF2F2", border: "#FECACA", color: "#991B1B", tag: "ALTA" },
  media: { bg: "#FFFBEB", border: "#FDE68A", color: "#92400E", tag: "MÉDIA" },
  baixa: { bg: "#EFF6FF", border: "#BFDBFE", color: "#1E40AF", tag: "BAIXA" },
};

export function RiskCallout({
  level,
  title,
  body,
}: RiskCalloutProps): JSX.Element {
  const s = STYLES[level];
  return (
    <div
      style={{
        background: s.bg,
        border: `1px solid ${s.border}`,
        borderRadius: 8,
        padding: "14px 18px",
        margin: "18px 0",
      }}
    >
      <div
        style={{
          fontFamily: "Geist Mono",
          fontSize: 10,
          color: s.color,
          letterSpacing: 1.5,
          fontWeight: 600,
          marginBottom: 6,
        }}
      >
        {s.tag}
      </div>
      <div
        style={{
          fontFamily: "Geist",
          fontSize: 15,
          fontWeight: 600,
          color: s.color,
          marginBottom: 6,
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontFamily: "Geist",
          fontSize: 14,
          color: s.color,
          opacity: 0.85,
          lineHeight: 1.6,
        }}
      >
        {body}
      </div>
    </div>
  );
}
