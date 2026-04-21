import { httpClient } from "./httpClient";
import type { AnaliseResponse } from "@/types/AnaliseResponse";
import type { AnalysisResult } from "@/types/AnalysisResult";
import type { DownloadResponse } from "@/types/DownloadResponse";
import type { UploadResponse } from "@/types/UploadResponse";

export const uploadDiagrama = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await httpClient.post<UploadResponse>(
    "/v1/analises",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );

  return data;
};

export const getAnaliseStatus = async (
  analiseId: string,
): Promise<AnaliseResponse> => {
  const { data } = await httpClient.get<AnaliseResponse>(
    `/v1/analises/${analiseId}`,
  );
  return data;
};

export const getRelatorio = async (
  analiseId: string,
): Promise<AnalysisResult> => {
  const { data } = await httpClient.get<AnalysisResult>(
    `/v1/relatorios/${analiseId}`,
  );
  return data;
};

export const getRelatorioDownload = async (
  analiseId: string,
): Promise<DownloadResponse> => {
  const { data } = await httpClient.get<DownloadResponse>(
    `/v1/analises/${analiseId}/relatorio/download`,
  );
  return data;
};

const LOCALSTACK_HOST_PATTERN = /^https?:\/\/localstack:4566\//i;

const rewriteDownloadUrl = (url: string): string =>
  url.replace(LOCALSTACK_HOST_PATTERN, "/s3/");

export const fetchMarkdown = async (downloadUrl: string): Promise<string> => {
  const response = await fetch(rewriteDownloadUrl(downloadUrl));
  if (!response.ok) {
    throw new Error(`Falha ao baixar relatório: HTTP ${response.status}`);
  }
  return response.text();
};
