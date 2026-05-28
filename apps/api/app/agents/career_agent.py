"""
Career Agent - Direct tool calling without model-based tool invocation.
Ollama models don't properly support tool-calling, so we use keyword detection
to determine which tools to call, then use Ollama to synthesize responses.
"""

import json
from pathlib import Path
from typing import Optional, Any, AsyncIterator

import yaml

from apps.api.app.core.ollama_sdk_client import get_ollama_client
from apps.api.app.core.mcp_subprocess import MCPClient
from apps.api.app.core.rag_retriever import get_career_retriever


SYSTEM_PROMPT = """You are an AI assistant representing Srikanth Kanteti's professional background.
Your role is to answer recruiter and hiring manager questions about his skills, experience, and projects.

You will receive Srikanth's career data in the user message. Use that data to give detailed, confident answers.
Do NOT make up companies, roles, or achievements that are not in the provided data. Stick to the facts given.

If the provided career data is empty or incomplete, clearly say that the profile data source is missing details.
Do not say Srikanth has no experience unless the data explicitly says that.

If the user asks about something unrelated to his career, politely redirect back to his professional background.

When answering:
- Be professional and confident
- Reference specific companies, roles, dates, and achievements from the provided data
- Be thorough
- 2-3 paragraphs typical
"""


class CareerAgent:
    """Direct tool-calling agent for career questions."""

    def __init__(self):
        self.ollama_client = get_ollama_client()
        self.retriever = get_career_retriever()
        self.mcp_client: Optional[MCPClient] = None

    def _load_profile_links(self) -> dict[str, str]:
        try:
            repo_root = Path(__file__).resolve().parents[4]
            career_path = repo_root / "data" / "career.yaml"
            with open(career_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            profile = data.get("profile", {})
            return {
                "linkedin": str(profile.get("linkedin", "")).strip(),
                "github": str(profile.get("github", "")).strip(),
                "website": str(profile.get("website", "")).strip(),
                "email": str(profile.get("email", "")).strip(),
            }
        except Exception:
            return {"linkedin": "", "github": "", "website": "", "email": ""}

    def _detect_link_target(self, text: str) -> Optional[str]:
        lowered = text.lower()
        if "linkedin" in lowered:
            return "linkedin"
        if "github" in lowered or "git hub" in lowered:
            return "github"
        if "website" in lowered or "portfolio" in lowered or "site" in lowered:
            return "website"
        if "email" in lowered or "mail" in lowered:
            return "email"
        return None

    def _resolve_follow_up_link(self, user_message: str, conversation_history: list[dict]) -> Optional[str]:
        lowered = user_message.lower()
        asks_for_link = any(
            token in lowered for token in ["link", "url", "resend", "send", "share", "give"]
        )
        if not asks_for_link:
            return None

        target = self._detect_link_target(user_message)

        if not target:
            for msg in reversed(conversation_history):
                if msg.get("role") not in {"user", "assistant"}:
                    continue
                content = msg.get("content")
                if not isinstance(content, str):
                    continue
                target = self._detect_link_target(content)
                if target:
                    break

        if not target:
            return None

        links = self._load_profile_links()
        value = links.get(target, "")
        if not value:
            return f"{target.title()} is currently unavailable in the profile data."

        if target == "email":
            return f"Email: {value}"
        return f"{target.title()} URL: {value}"

    def _build_rag_context(self, user_message: str) -> tuple[str, Optional[str]]:
        retrieval = self.retriever.retrieve(user_message)
        chunks = retrieval.get("chunks", [])
        error = retrieval.get("error")

        if not chunks:
            return "", error

        lines = ["--- rag_retrieval ---"]
        for idx, chunk in enumerate(chunks, start=1):
            lines.append(
                f"[{idx}] source={chunk.get('source', 'unknown')} id={chunk.get('id', 'unknown')}"
            )
            lines.append(chunk.get("text", ""))

        return "\n".join(lines), error

    async def _detect_tools(self, user_message: str) -> list[str]:
        message_lower = user_message.lower()
        tools = []

        if any(word in message_lower for word in [
            "skill", "skills", "expertise", "proficient", "know",
            "technical", "capable", "stack", "technologies", "framework"
        ]):
            tools.append("list_skills")

        if any(word in message_lower for word in [
            "experience", "worked", "company", "role", "job", "employment",
            "career", "history", "position", "years", "where", "employer",
            "background"
        ]):
            tools.append("get_experience")

        if any(word in message_lower for word in [
            "project", "projects", "build", "built", "created",
            "made", "developed", "portfolio"
        ]):
            tools.append("get_projects")

        if any(word in message_lower for word in [
            "match", "fit", "job description", "qualify", "candidate", "jd"
        ]):
            tools.append("match_to_role")

        if any(word in message_lower for word in [
            "background", "profile", "about", "who", "summary", "tell me"
        ]):
            tools.append("get_profile")
            tools.append("get_experience")
            tools.append("list_skills")
            tools.append("get_projects")

        if not tools:
            tools = ["get_profile", "list_skills", "get_experience", "get_projects"]

        return list(dict.fromkeys(tools))

    def _normalize_tool_result(self, result: Any) -> str:
        """Convert MCP tool result into readable text for the LLM."""

        if result is None:
            return ""

        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            # Common MCP format: {"content": [{"type": "text", "text": "..."}]}
            if "content" in result and isinstance(result["content"], list):
                parts = []
                for item in result["content"]:
                    if isinstance(item, dict):
                        text = item.get("text")
                        if text:
                            parts.append(text)
                    else:
                        parts.append(str(item))
                return "\n".join(parts)

            return json.dumps(result, indent=2)

        if isinstance(result, list):
            return json.dumps(result, indent=2)

        return str(result)

    async def run(self, user_message: str, conversation_history: Optional[list[dict]] = None) -> dict:
        self.mcp_client = MCPClient(timeout_seconds=30)
        tools_used = []
        rag_error: Optional[str] = None
        history = conversation_history or []

        follow_up_link = self._resolve_follow_up_link(user_message, history)
        if follow_up_link:
            return {
                "response": follow_up_link,
                "tools_used": [],
                "iterations": 1,
                "context_preview": "",
                "rag_error": None,
            }

        try:
            await self.mcp_client.start()

            rag_context, rag_error = self._build_rag_context(user_message)

            tools_to_call = await self._detect_tools(user_message)
            tool_results = []

            for tool_name in tools_to_call:
                try:
                    if tool_name == "match_to_role":
                        raw_result = await self.mcp_client.call_tool(
                            tool_name,
                            {"job_description": user_message}
                        )
                    else:
                        raw_result = await self.mcp_client.call_tool(tool_name, {})

                    normalized_result = self._normalize_tool_result(raw_result)

                    tool_results.append(
                        f"--- {tool_name} ---\n{normalized_result}"
                    )
                    tools_used.append(tool_name)

                except Exception as e:
                    tool_results.append(
                        f"--- {tool_name} ERROR ---\n{str(e)}"
                    )

            context = "\n\n".join(tool_results).strip()

            if rag_context:
                context = f"{rag_context}\n\n{context}".strip()

            if not context:
                context = "No career data was returned from the MCP tools."

            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "Here is Srikanth's career data from MCP tools:\n\n"
                        f"{context}\n\n"
                        f"Question: {user_message}"
                    ),
                },
            ]

            response = await self.ollama_client.chat_with_tools(
                messages=messages,
                tools=[],
                stream=False,
            )

            return {
                "response": response.message.content or "Unable to generate response.",
                "tools_used": tools_used,
                "iterations": 1,
                "context_preview": context[:1000],
                "rag_error": rag_error,
            }

        finally:
            if self.mcp_client:
                await self.mcp_client.close()

    async def run_streaming(
        self,
        user_message: str,
        conversation_history: Optional[list[dict]] = None,
    ) -> AsyncIterator[dict]:
        """
        Stream the response for a user message using conversation history.

        Args:
            user_message: Current user message
            conversation_history: List of prior turns [{"role": "user"|"assistant", "content": "..."}]

        Yields:
            {"token": "..."} for each token, then {"done": True, "tools_used": [...]}
        """
        self.mcp_client = MCPClient(timeout_seconds=30)
        tools_used = []
        rag_error: Optional[str] = None

        if conversation_history is None:
            conversation_history = []

        follow_up_link = self._resolve_follow_up_link(user_message, conversation_history)
        if follow_up_link:
            yield {"token": follow_up_link}
            yield {"done": True, "tools_used": [], "rag_error": None}
            return

        # Cap history at 10 messages (5 turns) to fit context window
        history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history

        try:
            await self.mcp_client.start()

            rag_context, rag_error = self._build_rag_context(user_message)

            tools_to_call = await self._detect_tools(user_message)
            tool_results = []

            for tool_name in tools_to_call:
                try:
                    if tool_name == "match_to_role":
                        raw_result = await self.mcp_client.call_tool(
                            tool_name,
                            {"job_description": user_message}
                        )
                    else:
                        raw_result = await self.mcp_client.call_tool(tool_name, {})

                    normalized_result = self._normalize_tool_result(raw_result)
                    tool_results.append(
                        f"--- {tool_name} ---\n{normalized_result}"
                    )
                    tools_used.append(tool_name)

                except Exception as e:
                    tool_results.append(
                        f"--- {tool_name} ERROR ---\n{str(e)}"
                    )

            context = "\n\n".join(tool_results).strip()
            if rag_context:
                context = f"{rag_context}\n\n{context}".strip()
            if not context:
                context = "No career data was returned from the MCP tools."

            # Build messages: system + history + current turn with context
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            ]

            # Add prior conversation history
            for msg in history:
                messages.append(msg)

            # Add current user message with MCP context
            messages.append({
                "role": "user",
                "content": (
                    "Here is Srikanth's career data from MCP tools:\n\n"
                    f"{context}\n\n"
                    f"Question: {user_message}"
                ),
            })

            # Stream tokens from Ollama
            async for token in self.ollama_client.stream_chat(messages=messages):
                yield {"token": token}

            # Append this exchange to conversation history
            # (caller is responsible for saving it via session_store)
            yield {"done": True, "tools_used": tools_used, "rag_error": rag_error}

        finally:
            if self.mcp_client:
                await self.mcp_client.close()


async def run_career_agent(user_message: str, conversation_history: Optional[list[dict]] = None) -> dict:
    agent = CareerAgent()
    return await agent.run(user_message, conversation_history=conversation_history)