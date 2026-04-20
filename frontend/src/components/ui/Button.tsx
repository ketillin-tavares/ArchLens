import {
  useState,
  type ButtonHTMLAttributes,
  type CSSProperties,
  type ReactNode,
} from "react";
import { TOKENS } from "@/config/tokens";

type ButtonVariant = "primary" | "accent" | "ghost" | "subtle" | "link";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "style"> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ReactNode;
  full?: boolean;
  style?: CSSProperties;
}

const SIZES: Record<ButtonSize, { h: number; px: number; fs: number }> = {
  sm: { h: 32, px: 12, fs: 13 },
  md: { h: 40, px: 16, fs: 14 },
  lg: { h: 48, px: 22, fs: 15 },
};

const VARIANTS: Record<
  ButtonVariant,
  { bg: string; color: string; border: string; hover: string }
> = {
  primary: {
    bg: TOKENS.navy,
    color: "#fff",
    border: `1px solid ${TOKENS.navy}`,
    hover: TOKENS.ink,
  },
  accent: {
    bg: TOKENS.blue,
    color: "#fff",
    border: `1px solid ${TOKENS.blue}`,
    hover: TOKENS.blueHover,
  },
  ghost: {
    bg: "transparent",
    color: TOKENS.ink,
    border: `1px solid ${TOKENS.line}`,
    hover: TOKENS.mist,
  },
  subtle: {
    bg: TOKENS.mist,
    color: TOKENS.ink,
    border: `1px solid ${TOKENS.line}`,
    hover: TOKENS.cloud,
  },
  link: {
    bg: "transparent",
    color: TOKENS.blue,
    border: "1px solid transparent",
    hover: "transparent",
  },
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  full,
  type = "button",
  disabled,
  style = {},
  onClick,
  ...rest
}: ButtonProps): JSX.Element {
  const [hover, setHover] = useState(false);
  const sz = SIZES[size];
  const vr = VARIANTS[variant];

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        height: sz.h,
        padding: `0 ${sz.px}px`,
        fontSize: sz.fs,
        background: disabled ? TOKENS.cloud : hover ? vr.hover : vr.bg,
        color: disabled ? TOKENS.slate : vr.color,
        border: vr.border,
        borderRadius: 8,
        fontFamily: "Geist, sans-serif",
        fontWeight: 500,
        letterSpacing: -0.1,
        cursor: disabled ? "not-allowed" : "pointer",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        width: full ? "100%" : "auto",
        transition: "background 120ms ease, transform 60ms ease",
        ...style,
      }}
      {...rest}
    >
      {icon}
      {children}
    </button>
  );
}
