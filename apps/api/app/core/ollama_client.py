import json
from pathlib import Path

import httpx
import yaml

from apps.api.app.core.config import settings

OLLAMA_URL = f"{settings.ollama_base_url}/api/chat"


def _load_profile_links() -> dict[str, str]:
    """Load stable profile links from data/career.yaml."""
    try:
        repo_root = Path(__file__).resolve().parents[4]
        career_path = repo_root / "data" / "career.yaml"
        with open(career_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        profile = data.get("profile", {})
        return {
            "email": str(profile.get("email", "")).strip(),
            "github": str(profile.get("github", "")).strip(),
            "linkedin": str(profile.get("linkedin", "")).strip(),
            "website": str(profile.get("website", "")).strip(),
        }
    except Exception:
        return {"email": "", "github": "", "linkedin": "", "website": ""}


def _build_system_prompt() -> str:
    links = _load_profile_links()
    links_json = json.dumps(links, ensure_ascii=True)
    return (
        "You are a personal profile assistant for Srikanth Kanteti. "
        "Answer using the profile data below and conversation history. "
        "Do not invent or substitute links. "
        "If user asks for a specific link (LinkedIn/GitHub/website/email), return exactly that field. "
        "If user asks follow-up like 'give the link' or 'send it' without naming it, resolve it from the previous turn intent and return the matching field. "
        "If a field is missing, say it is unavailable. "
        f"Profile links: {links_json}"
    )


def ask_ollama(message: str, history: list[dict] | None = None) -> str:
    history = history or []
    valid_history = [
        msg for msg in history[-6:]
        if msg.get("role") in {"user", "assistant"} and isinstance(msg.get("content"), str)
    ]

    payload = {
        "model": settings.ollama_model,
        "messages": [{"role": "system", "content": _build_system_prompt()}] + valid_history + [
            {"role": "user", "content": message}
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
