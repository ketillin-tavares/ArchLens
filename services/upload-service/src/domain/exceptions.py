class DomainError(Exception):
    """Exceção base para erros de domínio."""


class ArquivoInvalidoError(DomainError):
    """Lançada quando o tipo de arquivo enviado não é suportado."""


class ArquivoTamanhoExcedidoError(DomainError):
    """Lançada quando o arquivo excede o tamanho máximo permitido."""


class AnaliseNaoEncontradaError(DomainError):
    """Lançada quando uma análise não é encontrada no repositório."""


class RetentativaInvalidaError(DomainError):
    """Lançada quando uma retentativa de análise é solicitada para um status não elegível."""


class AnaliseNaoConcluidaError(DomainError):
    """Lançada quando uma operação exige análise concluída mas o status atual não é 'analisado'."""


class RelatorioIndisponivelError(DomainError):
    """Lançada quando o relatório Markdown não está disponível (s3_key ausente)."""
