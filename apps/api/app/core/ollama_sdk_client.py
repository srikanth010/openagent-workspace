"""
Async Ollama SDK client for tool-calling chat with LLMs.
Uses ollama.AsyncClient for proper async/await support.
"""

import ollama
from typing import Optional

from apps.api.app.core.config import settings


class OllamaSDKClient:
    """Wrapper around ollama.AsyncClient for tool-calling chat."""

    def __init__(self):
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)

    async def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        model: Optional[str] = None,
        stream: bool = False,
    ) -> ollama.ChatResponse:
        """
        Call Ollama chat API with tool definitions.

        Args:
            messages: List of message dicts with role/content
            tools: List of tool schema dicts (ollama.Tool format)
            model: Model name (defaults to config setting)
            stream: Whether to stream response

        Returns:
            ollama.ChatResponse with tool_calls in message if any were invoked
        """
        model = model or settings.career_model

        response = await self.client.chat(
            model=model,
            messages=messages,
            tools=tools,
            stream=stream,
        )

        return response


# Global instance
_ollama_client: Optional[OllamaSDKClient] = None


def get_ollama_client() -> OllamaSDKClient:
    """Get or create the global Ollama client."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaSDKClient()
    return _ollama_client
