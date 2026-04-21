import { useAuth } from "@clerk/clerk-react";
import { useEffect } from "react";
import { env } from "@/config/env";
import { setTokenProvider } from "@/services/httpClient";

export const useAuthSetup = (): void => {
  const { getToken } = useAuth();

  useEffect(() => {
    setTokenProvider(() =>
      getToken(
        env.clerkJwtTemplate ? { template: env.clerkJwtTemplate } : undefined,
      ),
    );
  }, [getToken]);
};
