import { TOKENS } from "@/config/tokens";

interface ComponentBreakdownProps {
  types?: Record<string, number> | null;
}

const SWATCHES = ["#0A2540", "#2563EB", "#60A5FA", "#93C5FD", "#BFDBFE"];

export function ComponentBreakdown({
  types,
}: ComponentBreakdownProps): JSX.Element {
  if (!types) {
    return (
      <div
        style={{
          background: "#fff",
          border: `1px solid ${TOKENS.line}`,
          borderRadius: 12,
          padding: "16px 20px",
          minHeight: 108,
        }}
      >
        <div
          style={{
            fontFamily: "Geist Mono",
            fontSize: 10,
            color: TOKENS.slate,
            letterSpacing: 1.5,
            textTransform: "uppercase",
          }}
        >
          Componentes por tipo
        </div>
        <div
          style={{
            height: 14,
            width: "60%",
            background: TOKENS.cloud,
            borderRadius: 4,
            marginTop: 14,
          }}
        />
        <div
          style={{
            height: 14,
            width: "40%",
            background: TOKENS.cloud,
            borderRadius: 4,
            marginTop: 10,
          }}
        />
      </div>
    );
  }

  const entries = Object.entries(types);
  const total = entries.reduce((acc, [, v]) => acc + v, 0) || 1;

  return (
    <div
      style={{
        background: "#fff",
        border: `1px solid ${TOKENS.line}`,
        borderRadius: 12,
        padding: "16px 20px",
        minHeight: 108,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      <div
        style={{
          fontFamily: "Geist Mono",
          fontSize: 10,
          color: TOKENS.slate,
          letterSpacing: 1.5,
          textTransform: "uppercase",
        }}
      >
        Componentes por tipo
      </div>
      <div
        style={{
          display: "flex",
          height: 10,
          borderRadius: 5,
          overflow: "hidden",
          background: TOKENS.cloud,
        }}
      >
        {entries.map(([k, v], i) => (
          <div
            key={k}
            style={{
              width: `${(v / total) * 100}%`,
              background: SWATCHES[i % SWATCHES.length],
            }}
            title={`${k}: ${v}`}
          />
        ))}
      </div>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "6px 16px",
          marginTop: "auto",
        }}
      >
        {entries.map(([k, v], i) => (
          <div
            key={k}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontFamily: "Geist Mono",
              fontSize: 12,
              color: TOKENS.ink,
            }}
          >
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: 2,
                background: SWATCHES[i % SWATCHES.length],
              }}
            />
            <span>{k}</span>
            <span style={{ color: TOKENS.slate }}>· {v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
