import httpx

from apps.api.app.core.config import settings

OLLAMA_URL = f"{settings.ollama_base_url}/api/chat"

def ask_ollama(message: str) -> str:
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI coding assistant."
            },
            {
                "role": "user",
                "content": message
            },
        ],
        "stream": False,
    }

    response = httpx.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]
