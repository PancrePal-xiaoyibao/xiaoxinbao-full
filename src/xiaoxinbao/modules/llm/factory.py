from __future__ import annotations

from xiaoxinbao.modules.llm.base import LLMGateway
from xiaoxinbao.modules.llm.mock import MockGateway
from xiaoxinbao.modules.llm.openai_compatible import OpenAICompatibleGateway
from xiaoxinbao.settings import Settings


def build_gateway(settings: Settings) -> LLMGateway:
    mode = settings.llm_mode.lower()
    if mode == "mock":
        return MockGateway()
    if mode == "fastgpt":
        if not settings.fastgpt_api_base:
            raise ValueError("FASTGPT_API_BASE is required when LLM_MODE=fastgpt")
        return OpenAICompatibleGateway(
            api_base=settings.fastgpt_api_base,
            api_key=settings.fastgpt_api_key,
            default_model=settings.model_name,
        )
    if mode == "direct":
        return OpenAICompatibleGateway(
            api_base=settings.openai_api_base,
            api_key=settings.openai_api_key,
            default_model=settings.model_name,
        )
    raise ValueError(f"Unsupported LLM_MODE: {settings.llm_mode}")
