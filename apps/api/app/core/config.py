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

    # Optional separate model for vision (multimodal) requests.
    ai_vision_model: str = ""
    # Optional speech-to-text model on an OpenAI-compatible /audio/transcriptions route.
    ai_transcription_model: str = ""

    # Embeddings — may point at a different endpoint than the chat model.
    embedding_provider: str = "openai_compatible"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""
    embedding_dimensions: int = 1536
    embedding_batch_size: int = 64

    # Retrieval
    vector_backend: str = "pgvector"
    chunk_size_words: int = 220
    chunk_overlap_words: int = 40
    retrieval_top_k: int = 6
    retrieval_min_score: float = 0.05

    # Uploads
    upload_dir: str = "./var/uploads"
    max_upload_mb: int = 20

    # Rate limiting (per client IP, sliding window)
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    ai_rate_limit_requests: int = 20
    ai_rate_limit_window_seconds: int = 60

    # Sandboxed code execution
    code_execution_enabled: bool = True
    code_execution_timeout_seconds: int = 8
    code_execution_max_output_chars: int = 20000
    code_execution_memory_mb: int = 256

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
