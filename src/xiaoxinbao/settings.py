from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "xiaoxinbao"
    app_env: str = "development"
    llm_mode: str = "mock"
    model_name: str = "mock-gpt"
    fastgpt_api_base: str | None = None
    fastgpt_api_key: str | None = None
    openai_api_base: str = "https://api.openai.com/v1"
    openai_api_key: str | None = None
    session_ttl_seconds: int = 1800
    session_history_limit: int = 10
    bot_names: list[str] = Field(default_factory=lambda: ["小馨宝"])
    group_trigger_keywords: list[str] = Field(default_factory=lambda: ["小馨宝", "心理", "求助"])
    knowledge_dir: str = "config/knowledge"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("bot_names", "group_trigger_keywords", mode="before")
    @classmethod
    def parse_csv_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return [str(value).strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
