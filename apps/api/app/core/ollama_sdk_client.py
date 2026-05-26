"""
Async Ollama SDK client wrapper using thread pool.
Uses ollama.Client (sync) in a thread pool to avoid blocking the event loop.
The AsyncClient in ollama library is broken for our use case, so we use sync + executor.
"""

import asyncio
import ollama
from typing import Optional

from apps.api.app.core.config import settings


class OllamaSDKClient:
    """Wrapper around ollama.Client using thread pool for async support."""

    def __init__(self):
        self.client = ollama.Client(host=settings.ollama_base_url)

    async def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        model: Optional[str] = None,
        stream: bool = False,
    ) -> ollama.ChatResponse:
        """
        Call Ollama chat API with tool definitions (runs in thread pool).

        Args:
            messages: List of message dicts with role/content
            tools: List of tool schema dicts (ollama.Tool format)
            model: Model name (defaults to config setting)
            stream: Whether to stream response

        Returns:
            ollama.ChatResponse with tool_calls in message if any were invoked
        """
        import functools

        model = model or settings.career_model

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            functools.partial(
                self.client.chat,
                model=model,
                messages=messages,
                tools=tools,
                stream=stream,
            ),
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
