import { SignedIn, SignedOut } from "@clerk/clerk-react";
import { useState } from "react";
import { TopBar, type AppPage } from "@/components/ui/TopBar";
import { SignInScreen } from "@/components/auth/SignInScreen";
import { NewAnalysisPage } from "@/pages/NewAnalysisPage";
import { ResultsPage } from "@/pages/ResultsPage";
import { useAuthSetup } from "@/hooks/useAuthSetup";

export function App(): JSX.Element {
  useAuthSetup();

  return (
    <>
      <SignedOut>
        <SignInScreen />
      </SignedOut>
      <SignedIn>
        <AuthenticatedApp />
      </SignedIn>
    </>
  );
}

function AuthenticatedApp(): JSX.Element {
  const [page, setPage] = useState<AppPage>("new");
  const [analiseId, setAnaliseId] = useState<string | null>(null);

  const handleStarted = (id: string): void => {
    setAnaliseId(id);
    setPage("results");
  };

  const handleNav = (next: AppPage): void => {
    setPage(next);
  };

  return (
    <>
      <TopBar page={page} onNav={handleNav} />
      {page === "new" && (
        <NewAnalysisPage
          onStarted={handleStarted}
          onCancel={() => setPage("new")}
        />
      )}
      {page === "results" &&
        (analiseId ? (
          <ResultsPage
            analiseId={analiseId}
            onNew={() => {
              setAnaliseId(null);
              setPage("new");
            }}
          />
        ) : (
          <EmptyResults onNew={() => setPage("new")} />
        ))}
    </>
  );
}

function EmptyResults({ onNew }: { onNew: () => void }): JSX.Element {
  return (
    <div
      style={{
        maxWidth: 640,
        margin: "0 auto",
        padding: "80px 28px",
        textAlign: "center",
        fontFamily: "Geist, sans-serif",
        color: "#475569",
      }}
    >
      <h2 style={{ color: "#0A2540", marginBottom: 8 }}>
        Nenhum relatório selecionado
      </h2>
      <p style={{ marginBottom: 20 }}>
        Envie um novo diagrama para gerar um relatório.
      </p>
      <button
        onClick={onNew}
        style={{
          background: "#2563EB",
          color: "#fff",
          border: "none",
          padding: "10px 18px",
          borderRadius: 8,
          cursor: "pointer",
          fontFamily: "Geist, sans-serif",
          fontSize: 14,
          fontWeight: 500,
        }}
      >
        Nova análise
      </button>
    </div>
  );
}
