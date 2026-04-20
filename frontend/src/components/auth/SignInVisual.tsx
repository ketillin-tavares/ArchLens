import { TOKENS } from "@/config/tokens";
import { ArchDiagram } from "./ArchDiagram";

export function SignInVisual(): JSX.Element {
  return (
    <div
      style={{
        position: "relative",
        overflow: "hidden",
        background: `linear-gradient(145deg, ${TOKENS.navy} 0%, #071A2E 100%)`,
        color: "#fff",
        padding: "56px 64px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <svg
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          opacity: 0.18,
        }}
        aria-hidden
      >
        <defs>
          <pattern
            id="grid"
            width="40"
            height="40"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M40 0H0V40"
              fill="none"
              stroke="#60A5FA"
              strokeWidth="0.5"
            />
          </pattern>
          <radialGradient id="glow" cx="50%" cy="40%" r="60%">
            <stop offset="0%" stopColor="#2563EB" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#2563EB" stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        <rect width="100%" height="100%" fill="url(#glow)" />
      </svg>

      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          gap: 10,
          fontFamily: "Geist Mono",
          fontSize: 11,
          color: "rgba(255,255,255,0.6)",
          letterSpacing: 1.5,
          textTransform: "uppercase",
        }}
      >
        <span
          style={{
            width: 6,
            height: 6,
            background: TOKENS.blue,
            borderRadius: 3,
            boxShadow: "0 0 12px #2563EB",
          }}
        />
        Varredura de Arquitetura · Ao Vivo
      </div>

      <div style={{ position: "relative", maxWidth: 460 }}>
        <h2
          style={{
            fontFamily: "Geist",
            fontWeight: 600,
            fontSize: 38,
            letterSpacing: -1.5,
            lineHeight: 1.1,
            margin: 0,
          }}
        >
          Veja sua arquitetura como um engenheiro sênior veria.
        </h2>
        <p
          style={{
            fontFamily: "Geist",
            fontSize: 15,
            color: "rgba(255,255,255,0.65)",
            lineHeight: 1.6,
            marginTop: 18,
          }}
        >
          Envie um diagrama. O ArchLens identifica os componentes, mapeia as conexões e aponta os riscos arquiteturais que causariam problemas em produção.
        </p>
      </div>

      <div style={{ position: "relative" }}>
        <ArchDiagram />
      </div>
    </div>
  );
}
