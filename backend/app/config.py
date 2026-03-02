from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://po_user:changeme@postgres:5432/po_pipeline"
    qdrant_url: str = "http://qdrant:6333"
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"
    secret_key: str = "dev-secret"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
