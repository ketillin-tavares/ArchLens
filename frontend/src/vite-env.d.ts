/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_KONG_BASE_URL: string;
  readonly VITE_CLERK_PUBLISHABLE_KEY: string;
  readonly VITE_CLERK_JWT_TEMPLATE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
