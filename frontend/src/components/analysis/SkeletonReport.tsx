import { TOKENS } from "@/config/tokens";

const ROWS = [60, 95, 88, 72, 90, 40];

export function SkeletonReport(): JSX.Element {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {ROWS.map((w, i) => (
        <div
          key={i}
          style={{
            height: 14,
            width: `${w}%`,
            background: TOKENS.cloud,
            borderRadius: 4,
          }}
        />
      ))}
    </div>
  );
}
