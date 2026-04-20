import { useState, type InputHTMLAttributes } from "react";
import { TOKENS } from "@/config/tokens";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export function TextField({
  label,
  hint,
  error,
  onFocus,
  onBlur,
  style,
  ...rest
}: TextFieldProps): JSX.Element {
  const [focus, setFocus] = useState(false);

  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {label && (
        <span style={{ fontSize: 13, fontWeight: 500, color: TOKENS.ink }}>
          {label}
        </span>
      )}
      <input
        {...rest}
        onFocus={(event) => {
          setFocus(true);
          onFocus?.(event);
        }}
        onBlur={(event) => {
          setFocus(false);
          onBlur?.(event);
        }}
        style={{
          height: 40,
          padding: "0 12px",
          fontSize: 14,
          color: TOKENS.ink,
          background: "#fff",
          border: `1px solid ${
            error ? TOKENS.bad : focus ? TOKENS.blue : TOKENS.line
          }`,
          borderRadius: 8,
          outline: "none",
          fontFamily: "Geist, sans-serif",
          boxShadow: focus ? `0 0 0 3px ${TOKENS.blueSoft}` : "none",
          transition: "border-color 100ms ease, box-shadow 100ms ease",
          ...(style ?? {}),
        }}
      />
      {hint && !error && (
        <span style={{ fontSize: 12, color: TOKENS.slate }}>{hint}</span>
      )}
      {error && (
        <span style={{ fontSize: 12, color: TOKENS.bad }}>{error}</span>
      )}
    </label>
  );
}
