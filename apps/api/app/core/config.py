from pydantic_settings import BaseSettings
import json


class Settings(BaseSettings):
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen35fast:latest"
    career_model: str = "qwen35fast:latest"
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://srikanthkanteti.com"
    ]

    class Config:
        env_file = ".env"

    def __init__(self, **data):
        super().__init__(**data)
        # Parse ALLOWED_ORIGINS if set as JSON string
        if isinstance(self.allowed_origins, str):
            try:
                self.allowed_origins = json.loads(self.allowed_origins)
            except json.JSONDecodeError:
                pass


settings = Settings()
