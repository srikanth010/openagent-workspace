from fastapi import APIRouter

from apps.api.app.core.config import settings

router = APIRouter(prefix="/config", tags=["Config"])

@router.get("")
def get_config():
    return {
        "ollama_base_url": settings.ollama_base_url,
        "ollama_model": settings.ollama_model,
    }
