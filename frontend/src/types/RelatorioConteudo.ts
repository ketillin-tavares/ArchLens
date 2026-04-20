import type { RiskSeverity } from "./RiskSeverity";

export interface RiscosPorSeveridade {
  critica: number;
  alta: number;
  media: number;
  baixa: number;
}

export interface RelatorioEstatisticas {
  total_componentes: number;
  total_riscos: number;
  riscos_por_severidade: RiscosPorSeveridade;
}

export interface RelatorioComponente {
  id: string;
  nome: string;
  tipo: string;
  confianca: number;
  metadata: Record<string, unknown>;
  processamento_id: string;
}

export interface RelatorioRisco {
  id: string;
  descricao: string;
  severidade: RiskSeverity;
  componentes_afetados: string[];
  recomendacao_descricao: string;
  recomendacao_prioridade: RiskSeverity;
  processamento_id: string;
}

export interface RelatorioConteudo {
  estatisticas: RelatorioEstatisticas;
  componentes: RelatorioComponente[];
  riscos: RelatorioRisco[];
}
