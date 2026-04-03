class DomainError(Exception):
    """Exceção base para erros de domínio."""


class ProcessamentoNaoEncontradoError(DomainError):
    """Lançada quando um processamento não é encontrado para a análise informada."""


class AIBaseError(Exception):
    """Exceção base para erros relacionados à IA."""


class LLMApiError(AIBaseError):
    """Exceção base para erros retriáveis do LLM."""


class LLMTimeoutError(LLMApiError):
    """Timeout na chamada ao LLM — retriável."""


class LLMRateLimitError(LLMApiError):
    """Rate limit atingido no LLM — retriável."""


class LLMContentFilterError(AIBaseError):
    """Resposta bloqueada por filtro de conteúdo — NÃO retriável."""


class LLMContextWindowError(AIBaseError):
    """Contexto excedeu o limite do modelo — NÃO retriável."""


class SchemaValidationError(AIBaseError):
    """Resposta do LLM inválida mesmo após correção — NÃO retriável."""


class AnaliseInsanaError(AIBaseError):
    """Resposta do LLM falhou nos sanity checks — NÃO retriável."""


class ImageProcessingError(AIBaseError):
    """Falha ao normalizar a imagem — NÃO retriável."""


class StorageDownloadError(AIBaseError):
    """Falha ao baixar arquivo do S3 — retriável."""
