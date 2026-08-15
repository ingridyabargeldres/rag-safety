"""Cliente ligero para el chat de OpenAI, usado como LLM de propósito
general en las etapas del ataque que requieren generación de texto:
respuestas adversarias y caminos de relaciones.
"""

from __future__ import annotations

import os
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, prompt: str, *, system: str | None = None) -> str: ...


class OpenAIClient:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None, temperature: float = 0.7):
        from dotenv import load_dotenv
        from openai import OpenAI  # imported lazily so the package is optional for tests

        load_dotenv()  # picks up .env in the working/repo directory, if present
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Export it or pass api_key= explicitly."
            )
        self._client = OpenAI(api_key=key)
        self.model = model
        self.temperature = temperature

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return response.choices[0].message.content or ""


class StaticLLMClient:
    """Cliente simulado y determinista para pruebas y demos: devuelve
    respuestas predefinidas."""

    def __init__(self, replies: list[str]):
        self._replies = list(replies)

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        if not self._replies:
            return ""
        return self._replies.pop(0)
