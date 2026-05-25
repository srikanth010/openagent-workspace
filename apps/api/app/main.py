from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.core.config import settings
from apps.api.app.routes.agent import router as agent_router
from apps.api.app.routes.career import router as career_router
from apps.api.app.routes.config import router as config_router
from apps.api.app.routes.health import router as health_router

app = FastAPI(
    title="OpenAgent Workspace API",
    version="0.1.0",
    description="Portfolio-grade AI agent system for tool use, RAG, workflows, and evaluation.",
)

# CORS middleware for Next.js frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)

app.include_router(health_router)
app.include_router(config_router)
app.include_router(agent_router)
app.include_router(career_router)

@app.get("/")
def root():
    return {
        "message": "OpenAgent Workspace API",
        "docs": "/docs",
        "health": "/health",
        "config": "/config",
        "agent_chat": "/agent/chat",
        "career_chat": "/career/chat",
    }
