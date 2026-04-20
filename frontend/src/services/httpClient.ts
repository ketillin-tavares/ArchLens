import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";
import { env } from "@/config/env";

type TokenGetter = () => Promise<string | null>;

let tokenGetter: TokenGetter | null = null;

export const setTokenProvider = (fn: TokenGetter): void => {
  tokenGetter = fn;
};

export class UnauthorizedError extends Error {
  constructor() {
    super("Sessão expirada ou não autorizada.");
    this.name = "UnauthorizedError";
  }
}

export class ApiError extends Error {
  public readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const httpClient: AxiosInstance = axios.create({
  baseURL: env.kongBaseUrl,
  withCredentials: true,
  timeout: 30_000,
  headers: {
    Accept: "application/json",
  },
});

httpClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    if (tokenGetter) {
      const token = await tokenGetter();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
);

httpClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    const status = error.response?.status ?? 0;

    if (status === 401) {
      return Promise.reject(new UnauthorizedError());
    }

    const detail =
      error.response?.data?.detail ??
      error.response?.data?.message ??
      error.message ??
      "Erro de rede";

    return Promise.reject(new ApiError(status, detail));
  },
);
