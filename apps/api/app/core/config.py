from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. All values come from the environment — never hard-coded."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "UniOS AI"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://unios:change-me@localhost:5432/unios"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    cors_origins: str = "http://localhost:3000"

    # AI layer — provider agnostic. Any OpenAI-compatible endpoint works:
    # OpenAI, OpenRouter, Groq, Together, vLLM, Ollama (/v1), LM Studio.
    ai_provider: str = "openai_compatible"
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_allow_keyless: bool = False
    ai_temperature: float = 0.3
    ai_max_output_tokens: int = 1200
    chat_history_limit: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
