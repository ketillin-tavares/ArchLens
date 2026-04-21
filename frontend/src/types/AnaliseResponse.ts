import type { AnaliseStatus } from "./AnaliseStatus";

export interface AnaliseResponse {
  id: string;
  diagrama_id: string;
  status: AnaliseStatus;
  erro_detalhe: string | null;
  relatorio_s3_key: string | null;
  criado_em: string;
  atualizado_em: string;
}
