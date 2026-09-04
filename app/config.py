from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação, carregadas do ambiente (.env)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Banco de dados
    database_url: str = "sqlite:///./gymflow.db"

    # JWT
    secret_key: str = "insecure-dev-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # IA
    ai_provider: str = "mock"  # "openai" ou "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # CORS
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
