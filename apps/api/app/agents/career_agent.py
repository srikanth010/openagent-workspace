"""
Career Agent - Direct tool calling without model-based tool invocation.
Ollama models don't properly support tool-calling, so we use keyword detection
to determine which tools to call, then use Ollama to synthesize responses.
"""

import json
import asyncio
from typing import Optional

from apps.api.app.core.ollama_sdk_client import get_ollama_client
from apps.api.app.core.mcp_subprocess import MCPClient

SYSTEM_PROMPT = """You are an AI assistant representing Srikanth Kanteti's professional background.
Your role is to answer recruiter and hiring manager questions about his skills, experience, and projects.

You have been provided with relevant career information. Use it to answer the user's question.
Be specific, professional, and cite concrete examples. Never fabricate information.

SCOPE: Stay strictly within the provided career data. If asked about unrelated topics (weather, sports,
general knowledge), politely decline and redirect back to his background.

When answering:
- Be professional and confident
- Cite specific examples and achievements
- Connect experience to relevant roles or companies
- Be brief but thorough (2-3 paragraphs typical)
"""


class CareerAgent:
    """Direct tool-calling agent for career questions."""

    def __init__(self):
        self.ollama_client = get_ollama_client()
        self.mcp_client: Optional[MCPClient] = None

    async def _detect_tools(self, user_message: str) -> list[str]:
        """Detect which tools to call based on user message keywords."""
        message_lower = user_message.lower()
        tools = []

        if any(word in message_lower for word in ['skill', 'expertise', 'proficient', 'know', 'technical', 'capable']):
            tools.append('list_skills')
        if any(word in message_lower for word in [
            'experience', 'worked', 'company', 'role', 'job', 'employment',
            'career', 'history', 'position', 'years', 'where', 'employer'
        ]):
            tools.append('get_experience')
        if any(word in message_lower for word in ['project', 'build', 'built', 'created', 'made', 'developed']):
            tools.append('get_projects')
        if any(word in message_lower for word in ['match', 'fit', 'job description', 'qualify', 'candidate']):
            tools.append('match_to_role')
        if any(word in message_lower for word in ['background', 'profile', 'about', 'who', 'summary', 'tell me']):
            tools.append('get_profile')
            # Background/about questions should also include experience
            tools.append('get_experience')

        if not tools:
            tools = ['get_profile', 'list_skills', 'get_experience']

        return list(set(tools))

    async def run(self, user_message: str) -> dict:
        """Run the agent for a single user message."""
        self.mcp_client = MCPClient(timeout_seconds=30)
        tools_used = []

        try:
            await self.mcp_client.start()

            # Detect and call tools
            tools_to_call = await self._detect_tools(user_message)
            tool_results = []

            for tool_name in tools_to_call:
                try:
                    if tool_name == 'match_to_role':
                        result = await self.mcp_client.call_tool(tool_name, {"job_description": user_message})
                    else:
                        result = await self.mcp_client.call_tool(tool_name, {})

                    tool_results.append(result)
                    tools_used.append(tool_name)
                except Exception as e:
                    tool_results.append(f"Error calling {tool_name}: {str(e)}")

            # Build context from tool results
            context = "\n".join(tool_results) if tool_results else "No tools were called."

            # Use Ollama to synthesize a response
            messages = [
                {
                    "role": "system",
                    "content": f"{SYSTEM_PROMPT}\n\nHere is Srikanth's career data:\n{context}"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]

            response = await self.ollama_client.chat_with_tools(
                messages=messages,
                tools=[],
                stream=False
            )

            return {
                "response": response.message.content or "Unable to generate response.",
                "tools_used": tools_used,
                "iterations": 1
            }

        finally:
            if self.mcp_client:
                await self.mcp_client.close()


async def run_career_agent(user_message: str) -> dict:
    """Entry point for the career agent."""
    agent = CareerAgent()
    return await agent.run(user_message)
