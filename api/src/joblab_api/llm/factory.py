"""Build an adapter from a provider enum + decrypted API key."""

from __future__ import annotations

from joblab_api.llm.adapters.anthropic import AnthropicAdapter
from joblab_api.llm.adapters.gemini import GeminiAdapter
from joblab_api.llm.adapters.openai import OpenAIAdapter
from joblab_api.llm.models import LLMProvider
from joblab_api.llm.provider import LLMAdapter


def build_adapter(provider: LLMProvider, api_key: str) -> LLMAdapter:
    if provider is LLMProvider.OPENAI:
        return OpenAIAdapter(api_key=api_key)
    if provider is LLMProvider.ANTHROPIC:
        return AnthropicAdapter(api_key=api_key)
    if provider is LLMProvider.GEMINI:
        return GeminiAdapter(api_key=api_key)
    raise ValueError(f"unknown provider: {provider}")
