import { ClerkProvider } from "@clerk/clerk-react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { env } from "./config/env";
import "./index.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Elemento #root não encontrado no index.html.");
}

createRoot(rootElement).render(
  <StrictMode>
    <ClerkProvider publishableKey={env.clerkPublishableKey}>
      <App />
    </ClerkProvider>
  </StrictMode>,
);
