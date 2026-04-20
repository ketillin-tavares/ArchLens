import { UserButton } from "@clerk/clerk-react";
import { TOKENS } from "@/config/tokens";
import { Wordmark } from "./Wordmark";

export type AppPage = "new" | "results";

interface TopBarProps {
  page: AppPage;
  onNav: (page: AppPage) => void;
}

const TABS: Array<{ key: AppPage; label: string }> = [
  { key: "new", label: "Nova análise" },
  { key: "results", label: "Relatórios" },
];

export function TopBar({ page, onNav }: TopBarProps): JSX.Element {
  return (
    <header
      style={{
        height: 64,
        borderBottom: `1px solid ${TOKENS.line}`,
        background: "#fff",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 28px",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
        <Wordmark size={18} onClick={() => onNav("new")} />
        <nav style={{ display: "flex", gap: 4 }}>
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => onNav(t.key)}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "8px 12px",
                borderRadius: 6,
                fontFamily: "Geist",
                fontSize: 14,
                fontWeight: 500,
                color: page === t.key ? TOKENS.navy : TOKENS.slate,
                position: "relative",
              }}
            >
              {t.label}
              {page === t.key && (
                <span
                  style={{
                    position: "absolute",
                    left: 12,
                    right: 12,
                    bottom: -17,
                    height: 2,
                    background: TOKENS.navy,
                  }}
                />
              )}
            </button>
          ))}
        </nav>
      </div>
      <UserButton
        afterSignOutUrl="/"
        appearance={{
          elements: {
            avatarBox: { width: 32, height: 32 },
            userButtonPopoverCard: {
              borderRadius: 10,
              border: `1px solid ${TOKENS.line}`,
            },
            userButtonPopoverActionButton: {
              fontFamily: "Geist, sans-serif",
            },
          },
        }}
      />
    </header>
  );
}
