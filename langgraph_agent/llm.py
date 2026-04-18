from __future__ import annotations

import os

from langchain_ollama import ChatOllama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
SECOND_MODEL = os.getenv("OLLAMA_SECOND_MODEL", "mistral")  # override with glm-4.7-flash if pulled


def get_llm(model: str | None = None, temperature: float = 0.0, seed: int = 42) -> ChatOllama:
    return ChatOllama(
        model=model or DEFAULT_MODEL,
        temperature=temperature,
        base_url=OLLAMA_HOST,
        # Pass seed via num_ctx workaround — actual seed set in options at call time
    )


def get_second_llm() -> ChatOllama:
    """Return the second-opinion LLM used by reclassify_node."""
    return get_llm(model=SECOND_MODEL)
