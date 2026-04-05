"""
Guardrail: Detecta tentativas de prompt injection.

Roda em pre_call — analisa o conteúdo do prompt ANTES de enviar ao LLM.

Diagramas de arquitetura podem conter texto embutido na imagem que o
modelo vision lê. Um atacante poderia criar um diagrama com texto como
"ignore previous instructions..." para manipular a análise.

Este guardrail detecta padrões comuns de injection no texto do prompt.
NÃO analisa a imagem em si (isso seria outra chamada LLM), mas protege
contra injection via texto do user message.
"""

import re
from typing import Optional, Union

from litellm.integrations.custom_guardrail import CustomGuardrail


# Padrões de prompt injection em português e inglês
INJECTION_PATTERNS = [
    # Inglês
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above\s+instructions",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?(your|the)\s+instructions",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+if\s+you",
    r"pretend\s+(you\s+are|to\s+be)",
    r"override\s+(your|the)\s+system",
    r"new\s+instructions?\s*:",
    r"system\s*:\s*you\s+are",
    r"do\s+not\s+follow\s+(the\s+)?schema",
    r"instead\s+of\s+json",
    r"don'?t\s+return\s+json",
    # Português
    r"ignore\s+(todas?\s+)?(as\s+)?instru[çc][õo]es\s+anteriores",
    r"desconsidere\s+(todas?\s+)?(as\s+)?instru[çc][õo]es",
    r"esque[çc]a\s+(todas?\s+)?(as\s+)?instru[çc][õo]es",
    r"voc[êe]\s+agora\s+[ée]",
    r"finja\s+(ser|que)",
    r"novas?\s+instru[çc][õo]es\s*:",
    r"n[ãa]o\s+retorne\s+json",
    r"n[ãa]o\s+siga\s+o\s+schema",
]

COMPILED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS
]


class PromptInjectionDetector(CustomGuardrail):
    """Detecta prompt injection no texto antes de enviar ao LLM."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def async_pre_call_hook(
        self,
        user_api_key_dict,
        cache,
        data: dict,
        call_type,
    ) -> Optional[Union[Exception, str, dict]]:
        """Analisa mensagens do usuário antes de enviar ao LLM."""
        messages = data.get("messages", [])

        for message in messages:
            if message.get("role") != "user":
                continue

            content = message.get("content", "")

            # Content pode ser string ou lista (multimodal)
            texts_to_check = []
            if isinstance(content, str):
                texts_to_check.append(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        texts_to_check.append(part.get("text", ""))

            for text in texts_to_check:
                for pattern in COMPILED_PATTERNS:
                    match = pattern.search(text)
                    if match:
                        raise ValueError(
                            f"Guardrail prompt_injection: possível tentativa de "
                            f"prompt injection detectada. "
                            f"Padrão: '{match.group()}'"
                        )

        return data
