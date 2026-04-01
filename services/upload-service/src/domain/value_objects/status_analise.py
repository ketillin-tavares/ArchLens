import enum


class StatusAnalise(enum.StrEnum):
    """Status possíveis de uma análise de diagrama."""

    RECEBIDO = "recebido"
    EM_PROCESSAMENTO = "em_processamento"
    ANALISADO = "analisado"
    ERRO = "erro"

    @classmethod
    def ordem(cls) -> dict["StatusAnalise", int]:
        """Retorna a ordem de progressão dos status para controle de idempotência."""
        return {
            cls.RECEBIDO: 0,
            cls.EM_PROCESSAMENTO: 1,
            cls.ANALISADO: 2,
            cls.ERRO: 2,
        }

    def pode_transitar_para(self, novo_status: "StatusAnalise") -> bool:
        """Verifica se a transição de status é válida (não regredir)."""
        ordem = self.ordem()
        return ordem[novo_status] > ordem[self]
