import type { ReactNode } from "react";
import { TOKENS } from "@/config/tokens";

type ScoreTone = "default" | "good" | "warn" | "bad";

interface ScoreCardProps {
  value: ReactNode;
  label: string;
  sub: ReactNode;
  tone?: ScoreTone;
  highlight?: boolean;
  span?: number;
}

const TONE_COLORS: Record<ScoreTone, string> = {
  default: TOKENS.navy,
  good: TOKENS.ok,
  warn: TOKENS.warn,
  bad: TOKENS.bad,
};

export function ScoreCard({
  value,
  label,
  sub,
  tone = "default",
  highlight,
  span = 1,
}: ScoreCardProps): JSX.Element {
  return (
    <div
      style={{
        gridColumn: `span ${span}`,
        background: highlight ? TOKENS.navy : "#fff",
        color: highlight ? "#fff" : TOKENS.ink,
        border: `1px solid ${highlight ? TOKENS.navy : TOKENS.line}`,
        borderRadius: 12,
        padding: "18px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        minHeight: 108,
      }}
    >
      <div
        style={{
          fontFamily: "Geist Mono",
          fontSize: 10,
          letterSpacing: 1.5,
          textTransform: "uppercase",
          color: highlight ? "rgba(255,255,255,0.6)" : TOKENS.slate,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: "Geist",
          fontWeight: 600,
          fontSize: 38,
          letterSpacing: -1.5,
          lineHeight: 1,
          color: highlight ? "#fff" : TONE_COLORS[tone],
        }}
      >
        {value}
      </div>
      <div
        style={{
          fontFamily: "Geist Mono",
          fontSize: 11,
          color: highlight ? "rgba(255,255,255,0.6)" : TOKENS.slate,
          marginTop: "auto",
        }}
      >
        {sub}
      </div>
    </div>
  );
}
