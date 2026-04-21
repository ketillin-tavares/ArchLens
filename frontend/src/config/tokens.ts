export const TOKENS = {
  navy: "#0A2540",
  ink: "#0F172A",
  blue: "#2563EB",
  blueHover: "#1D4ED8",
  blueSoft: "#EFF6FF",
  mist: "#F8FAFC",
  cloud: "#F1F5F9",
  line: "#E2E8F0",
  slate: "#64748B",
  slate2: "#475569",
  text: "#0F172A",
  ok: "#059669",
  warn: "#D97706",
  bad: "#DC2626",
} as const;

export type TokenKey = keyof typeof TOKENS;
