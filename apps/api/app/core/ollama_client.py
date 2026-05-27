import httpx

from apps.api.app.core.config import settings

OLLAMA_URL = f"{settings.ollama_base_url}/api/chat"

def ask_ollama(message: str) -> str:
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {
                "role": "system",
                "content": "You are a personal profile assistant. Answer using available profile and project data. If data is missing, state that clearly and ask a focused follow-up question. Do not invent facts outside the provided profile context."
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
