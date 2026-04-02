class DomainError(Exception):
    """Exceção base para erros de domínio."""


class RelatorioNaoEncontradoError(DomainError):
    """Lançada quando um relatório não é encontrado para a análise informada."""
