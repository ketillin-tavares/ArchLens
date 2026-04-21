import { TOKENS } from "@/config/tokens";

interface ArchLensMarkProps {
  size?: number;
  color?: string;
  accent?: string;
}

export function ArchLensMark({
  size = 32,
  color = TOKENS.navy,
  accent = TOKENS.blue,
}: ArchLensMarkProps): JSX.Element {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M20 32 L6 25 L20 18 L34 25 Z" fill={color} opacity="0.35" />
      <path d="M20 24 L6 17 L20 10 L34 17 Z" fill={color} opacity="0.65" />
      <path d="M20 16 L8 10 L20 4 L32 10 Z" fill={color} />
      <path
        d="M6 17 L20 24 L34 17"
        stroke={accent}
        strokeWidth="1.5"
        strokeLinecap="square"
      />
    </svg>
  );
}
