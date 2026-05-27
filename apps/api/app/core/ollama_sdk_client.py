"""
Async Ollama SDK client wrapper using thread pool.
Uses ollama.Client (sync) in a thread pool to avoid blocking the event loop.
The AsyncClient in ollama library is broken for our use case, so we use sync + executor.
"""

import asyncio
import ollama
import threading
from typing import Optional, AsyncIterator

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

    async def stream_chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion tokens from Ollama.
        Bridges sync Ollama streaming to async via queue + thread.

        Args:
            messages: List of message dicts with role/content
            model: Model name (defaults to config setting)

        Yields:
            Token strings as they are generated
        """
        model = model or settings.career_model
        token_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def _run_in_thread():
            try:
                for chunk in self.client.chat(
                    model=model,
                    messages=messages,
                    stream=True,
                ):
                    token = chunk.message.content or ""
                    if token:
                        loop.call_soon_threadsafe(token_queue.put_nowait, token)
            except Exception as e:
                loop.call_soon_threadsafe(token_queue.put_nowait, f"[ERROR: {str(e)}]")
            finally:
                loop.call_soon_threadsafe(token_queue.put_nowait, None)

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()

        while True:
            token = await token_queue.get()
            if token is None:
                break
            yield token


# Global instance
_ollama_client: Optional[OllamaSDKClient] = None


def get_ollama_client() -> OllamaSDKClient:
    """Get or create the global Ollama client."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaSDKClient()
    return _ollama_client
