from apps.api.app.core.ollama_client import ask_ollama

def run_chat_agent(message: str) -> str:
    return ask_ollama(message)
