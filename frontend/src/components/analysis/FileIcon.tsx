import { TOKENS } from "@/config/tokens";

interface FileIconProps {
  ext: string;
}

const PALETTE: Record<
  string,
  { bg: string; fg: string; label: string }
> = {
  png: { bg: "#EFF6FF", fg: TOKENS.blue, label: "PNG" },
  jpg: { bg: "#EFF6FF", fg: TOKENS.blue, label: "JPG" },
  jpeg: { bg: "#EFF6FF", fg: TOKENS.blue, label: "JPG" },
  pdf: { bg: "#FEF2F2", fg: TOKENS.bad, label: "PDF" },
};

export function FileIcon({ ext }: FileIconProps): JSX.Element {
  const p = PALETTE[ext] ?? {
    bg: TOKENS.cloud,
    fg: TOKENS.slate,
    label: "FILE",
  };
  return (
    <div
      style={{
        width: 40,
        height: 48,
        borderRadius: 6,
        background: p.bg,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "Geist Mono",
        fontSize: 10,
        fontWeight: 600,
        color: p.fg,
        border: `1px solid ${p.fg}22`,
        flexShrink: 0,
      }}
    >
      {p.label}
    </div>
  );
}
