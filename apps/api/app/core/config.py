from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    career_model: str = "qwen2.5-coder:7b"
    rag_enabled: bool = True
    rag_top_k: int = 4
    rag_embedding_model: str = "nomic-embed-text"
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://srikanthkanteti.com"
    ]

    def __init__(self, **data):
        super().__init__(**data)
        # Parse ALLOWED_ORIGINS if set as JSON string
        if isinstance(self.allowed_origins, str):
            try:
                self.allowed_origins = json.loads(self.allowed_origins)
            except json.JSONDecodeError:
                pass


settings = Settings()
