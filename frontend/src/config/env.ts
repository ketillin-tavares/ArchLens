export const env = {
  kongBaseUrl: import.meta.env.VITE_KONG_BASE_URL,
  clerkPublishableKey: import.meta.env.VITE_CLERK_PUBLISHABLE_KEY,
  clerkJwtTemplate: import.meta.env.VITE_CLERK_JWT_TEMPLATE,
} as const;

if (!env.kongBaseUrl) {
  throw new Error("VITE_KONG_BASE_URL não configurada.");
}

if (!env.clerkPublishableKey) {
  throw new Error("VITE_CLERK_PUBLISHABLE_KEY não configurada.");
}
