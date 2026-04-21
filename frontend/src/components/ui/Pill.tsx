import type { CSSProperties, ReactNode } from "react";
import { TOKENS } from "@/config/tokens";

type PillTone = "neutral" | "blue" | "good" | "warn" | "bad";

interface PillProps {
  children: ReactNode;
  tone?: PillTone;
  style?: CSSProperties;
}

const TONES: Record<PillTone, { bg: string; color: string; border: string }> =
  {
    neutral: { bg: TOKENS.mist, color: TOKENS.slate2, border: TOKENS.line },
    blue: { bg: TOKENS.blueSoft, color: TOKENS.blue, border: "#DBEAFE" },
    good: { bg: "#ECFDF5", color: TOKENS.ok, border: "#A7F3D0" },
    warn: { bg: "#FFFBEB", color: TOKENS.warn, border: "#FDE68A" },
    bad: { bg: "#FEF2F2", color: TOKENS.bad, border: "#FECACA" },
  };

export function Pill({
  children,
  tone = "neutral",
  style = {},
}: PillProps): JSX.Element {
  const t = TONES[tone];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "3px 10px",
        borderRadius: 999,
        background: t.bg,
        color: t.color,
        border: `1px solid ${t.border}`,
        fontFamily: "Geist Mono, monospace",
        fontSize: 11,
        fontWeight: 500,
        letterSpacing: 0.2,
        ...style,
      }}
    >
      {children}
    </span>
  );
}
