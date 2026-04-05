"""
Guardrail: Valida que a resposta do LLM é JSON válido.

Roda em post_call — intercepta a resposta ANTES de chegar no processing-service.
Se o LLM retornar texto livre, markdown, ou JSON quebrado, este guardrail
rejeita a resposta e força o LiteLLM a tentar o fallback.

Isso evita que o processing-service receba lixo e tenha que gastar
uma chamada extra de correção.
"""

import json
import re

import litellm
from litellm.integrations.custom_guardrail import CustomGuardrail


class JsonResponseValidator(CustomGuardrail):
    """Rejeita respostas do LLM que não são JSON válido."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def async_post_call_success_hook(
        self,
        data: dict,
        user_api_key_dict,
        response,
    ):
        """Verifica se a resposta é JSON válido após o LLM responder."""
        if not isinstance(response, litellm.ModelResponse):
            return

        for choice in response.choices:
            content = choice.message.content
            if not content:
                continue

            # Limpar markdown code blocks se o LLM envolveu em ```json ... ```
            cleaned = content.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Guardrail json_validator: resposta do LLM não é JSON válido. "
                    f"Erro: {e}. Primeiros 200 chars: {content[:200]}"
                )

            # Verificar estrutura mínima esperada (componentes e/ou riscos)
            if isinstance(parsed, dict):
                has_componentes = "componentes" in parsed
                has_riscos = "riscos" in parsed
                if not has_componentes and not has_riscos:
                    raise ValueError(
                        "Guardrail json_validator: JSON não contém 'componentes' nem 'riscos'. "
                        f"Keys encontradas: {list(parsed.keys())}"
                    )

            # Se passou, substituir o content limpo (sem markdown) na resposta
            choice.message.content = cleaned
