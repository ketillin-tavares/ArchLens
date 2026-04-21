import { SignIn } from "@clerk/clerk-react";
import { TOKENS } from "@/config/tokens";
import { Wordmark } from "@/components/ui/Wordmark";
import { SignInVisual } from "./SignInVisual";

export function SignInScreen(): JSX.Element {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        background: "#fff",
      }}
    >
      <div
        style={{
          padding: "56px 64px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Wordmark size={18} />

        <div style={{ margin: "auto 0", maxWidth: 400, width: "100%" }}>
          <div
            style={{
              fontFamily: "Geist Mono",
              fontSize: 11,
              color: TOKENS.slate,
              letterSpacing: 1.5,
              textTransform: "uppercase",
              marginBottom: 8,
            }}
          >
            Bem-vindo de volta
          </div>
          <h1
            style={{
              fontFamily: "Geist",
              fontWeight: 600,
              fontSize: 32,
              color: TOKENS.navy,
              letterSpacing: -1,
              margin: "0 0 8px",
            }}
          >
            Entrar no ArchLens
          </h1>
          <p
            style={{
              fontFamily: "Geist",
              fontSize: 15,
              color: TOKENS.slate2,
              margin: "0 0 32px",
              lineHeight: 1.5,
            }}
          >
            Analise seus diagramas de arquitetura. Obtenha um relatório de riscos em segundos.
          </p>

          <SignIn
            appearance={{
              variables: {
                colorPrimary: TOKENS.navy,
                colorText: TOKENS.ink,
                colorTextSecondary: TOKENS.slate2,
                colorBackground: "#ffffff",
                colorInputBackground: "#ffffff",
                colorInputText: TOKENS.ink,
                colorDanger: TOKENS.bad,
                colorSuccess: TOKENS.ok,
                colorWarning: TOKENS.warn,
                borderRadius: "8px",
                fontFamily:
                  '"Geist", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif',
                fontFamilyButtons: '"Geist", -apple-system, system-ui, sans-serif',
                fontSize: "14px",
              },
              elements: {
                rootBox: { width: "100%" },
                cardBox: { boxShadow: "none", border: "none", width: "100%" },
                card: {
                  boxShadow: "none",
                  border: "none",
                  padding: 0,
                  background: "transparent",
                  width: "100%",
                },
                header: { display: "none" },
                footer: { display: "none" },
                socialButtons: { display: "none" },
                socialButtonsBlockButton: { display: "none" },
                dividerRow: { display: "none" },
                formFieldLabel: {
                  fontSize: "13px",
                  fontWeight: 500,
                  color: TOKENS.ink,
                  marginBottom: "6px",
                },
                formFieldInput: {
                  height: "40px",
                  padding: "0 12px",
                  fontSize: "14px",
                  color: TOKENS.ink,
                  background: "#fff",
                  border: `1px solid ${TOKENS.line}`,
                  borderRadius: "8px",
                  transition:
                    "border-color 100ms ease, box-shadow 100ms ease",
                  "&:focus": {
                    borderColor: TOKENS.blue,
                    boxShadow: `0 0 0 3px ${TOKENS.blueSoft}`,
                    outline: "none",
                  },
                },
                formButtonPrimary: {
                  height: "48px",
                  fontSize: "15px",
                  fontWeight: 500,
                  letterSpacing: "-0.1px",
                  background: TOKENS.navy,
                  color: "#fff",
                  border: `1px solid ${TOKENS.navy}`,
                  borderRadius: "8px",
                  textTransform: "none",
                  transition: "background 120ms ease",
                  boxShadow: "none",
                  "&:hover": { background: TOKENS.ink },
                  "&:focus": { background: TOKENS.ink, boxShadow: "none" },
                  "&:active": { background: TOKENS.ink },
                },
                formFieldAction: { color: TOKENS.blue, fontWeight: 500 },
                formFieldHintText: {
                  color: TOKENS.slate,
                  fontSize: "12px",
                },
                formFieldErrorText: {
                  color: TOKENS.bad,
                  fontSize: "12px",
                },
                identityPreviewEditButton: { color: TOKENS.blue },
                footerActionLink: {
                  color: TOKENS.blue,
                  fontWeight: 500,
                },
                otpCodeFieldInput: {
                  borderColor: TOKENS.line,
                  "&:focus": {
                    borderColor: TOKENS.blue,
                    boxShadow: `0 0 0 3px ${TOKENS.blueSoft}`,
                  },
                },
                alert: { borderRadius: "8px" },
              },
            }}
          />
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontFamily: "Geist Mono",
            fontSize: 11,
            color: TOKENS.slate,
          }}
        >
          <span>© 2026 ArchLens</span>
          <span>Protegido pela Clerk</span>
        </div>
      </div>

      <SignInVisual />
    </div>
  );
}
