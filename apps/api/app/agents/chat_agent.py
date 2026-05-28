from apps.api.app.core.ollama_client import ask_ollama

def run_chat_agent(message: str, history: list[dict] | None = None) -> str:
    return ask_ollama(message, history=history)
