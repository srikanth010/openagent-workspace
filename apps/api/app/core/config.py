from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5-coder:32b"
    career_model: str = "qwen2.5-coder:32b"
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://srikanthkanteti.com"
    ]

    class Config:
        env_file = ".env"


settings = Settings()
