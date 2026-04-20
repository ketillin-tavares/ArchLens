import { TOKENS } from "@/config/tokens";
import { ArchLensMark } from "./ArchLensMark";

interface WordmarkProps {
  size?: number;
  color?: string;
  onClick?: () => void;
}

export function Wordmark({
  size = 22,
  color = TOKENS.navy,
  onClick,
}: WordmarkProps): JSX.Element {
  return (
    <div
      onClick={onClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 10,
        cursor: onClick ? "pointer" : "default",
      }}
    >
      <ArchLensMark size={size + 10} color={color} />
      <span
        style={{
          fontFamily: "Geist, sans-serif",
          fontWeight: 600,
          fontSize: size,
          color,
          letterSpacing: -0.6,
        }}
      >
        ArchLens
      </span>
    </div>
  );
}
