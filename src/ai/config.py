"""Configuration for AI article generation."""

from pydantic_settings import BaseSettings


class AIConfig(BaseSettings):
    """AI service configuration."""

    provider: str = "openai"  # openai, anthropic
    api_key: str = ""
    model: str = "gpt-4-turbo-preview"
    max_tokens: int = 500
    temperature: float = 0.7
    enable_cache: bool = True

    class Config:
        env_prefix = "AI_"
