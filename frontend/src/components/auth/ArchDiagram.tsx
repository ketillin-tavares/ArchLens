interface Node {
  x: number;
  y: number;
  label: string;
  sub: string;
  accent?: boolean;
}

const NODES: Node[] = [
  { x: 80, y: 90, label: "gateway", sub: "api" },
  { x: 200, y: 60, label: "auth", sub: "service" },
  { x: 200, y: 140, label: "orders", sub: "service" },
  { x: 360, y: 90, label: "postgres", sub: "database", accent: true },
];

export function ArchDiagram(): JSX.Element {
  return (
    <svg
      viewBox="0 0 480 180"
      style={{ width: "100%", maxWidth: 480, display: "block" }}
    >
      <g
        stroke="#60A5FA"
        strokeWidth="1"
        strokeDasharray="3 3"
        fill="none"
        opacity="0.6"
      >
        <path d="M80 90 L200 60" />
        <path d="M80 90 L200 140" />
        <path d="M200 60 L360 90" />
        <path d="M200 140 L360 90" />
        <path d="M200 60 L200 140" />
      </g>
      <path
        d="M200 60 L200 140"
        stroke="#F59E0B"
        strokeWidth="2"
        strokeDasharray="4 4"
        fill="none"
      />
      <text
        x="208"
        y="104"
        fill="#F59E0B"
        fontFamily="Geist Mono"
        fontSize="10"
      >
        risco: acoplamento
      </text>

      {NODES.map((n, i) => (
        <g key={i}>
          <rect
            x={n.x - 42}
            y={n.y - 18}
            width="84"
            height="36"
            rx="6"
            fill={n.accent ? "#2563EB" : "rgba(255,255,255,0.08)"}
            stroke={n.accent ? "#60A5FA" : "rgba(255,255,255,0.25)"}
          />
          <text
            x={n.x}
            y={n.y - 1}
            textAnchor="middle"
            fill="#fff"
            fontFamily="Geist"
            fontWeight="600"
            fontSize="12"
          >
            {n.label}
          </text>
          <text
            x={n.x}
            y={n.y + 12}
            textAnchor="middle"
            fill="rgba(255,255,255,0.5)"
            fontFamily="Geist Mono"
            fontSize="9"
          >
            {n.sub}
          </text>
        </g>
      ))}
    </svg>
  );
}
