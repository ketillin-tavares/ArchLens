import type { RelatorioConteudo } from "./RelatorioConteudo";

export interface AnalysisResult {
  id: string;
  analise_id: string;
  titulo: string;
  resumo: string;
  conteudo: RelatorioConteudo;
  s3_key: string | null;
  criado_em: string;
}
