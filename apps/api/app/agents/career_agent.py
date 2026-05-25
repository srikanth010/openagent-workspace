"""
Career Agent - Tool-calling agent loop using MCP tools and Ollama.
Handles multi-turn conversations with tool invocation.
"""

import json
import asyncio
from typing import Optional

from apps.api.app.core.ollama_sdk_client import get_ollama_client
from apps.api.app.core.mcp_subprocess import MCPClient


# Tool schemas for Ollama (hardcoded to avoid round-trip to MCP server)
CAREER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_profile",
            "description": "Get Srikanth's professional profile and summary",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_skills",
            "description": "List Srikanth's technical skills, optionally filtered by category",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Skill category filter",
                        "enum": [
                            "ai_ml",
                            "systems_architecture",
                            "leadership",
                            "backend_languages",
                            "frontend_stack",
                            "infrastructure"
                        ]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_experience",
            "description": "Get Srikanth's work experience, optionally filtered by company",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "Company name to filter by"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_projects",
            "description": "Get Srikanth's projects, optionally filtered by technology",
            "parameters": {
                "type": "object",
                "properties": {
                    "tech": {
                        "type": "string",
                        "description": "Technology to filter by"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "match_to_role",
            "description": "Match Srikanth's background to a job description",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_description": {
                        "type": "string",
                        "description": "Job description or role summary"
                    }
                },
                "required": ["job_description"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are an AI assistant representing Srikanth Kanteti's professional background.
Your role is to answer recruiter and hiring manager questions about his skills, experience, and projects.

Use the available tools to fetch accurate information from his profile. Be specific, use concrete examples,
and highlight relevant experience for the question being asked. Never fabricate information — if a tool
returns no relevant data, say so honestly.

When answering:
- Be professional and confident
- Cite specific examples and achievements
- Connect his experience to the role or company when relevant
- Highlight how his systems thinking translates to AI/ML domains
- Be brief but thorough (2-3 paragraphs typical)

IMPORTANT: After using tools to gather information, generate a final answer to the user's question.
Do not call tools repeatedly for the same information. When you have enough context, synthesize a response.
"""

MAX_ITERATIONS = 10


class CareerAgent:
    """Tool-calling agent for career-related questions."""

    def __init__(self):
        self.ollama_client = get_ollama_client()
        self.mcp_client: Optional[MCPClient] = None

    async def run(self, user_message: str) -> dict:
        """
        Run the agent for a single user message.

        Args:
            user_message: The user's question

        Returns:
            Dict with keys: response, tools_used, iterations
        """
        self.mcp_client = MCPClient(timeout_seconds=30)

        try:
            await self.mcp_client.start()

            messages = [
                {
                    "role": "user",
                    "content": user_message
                }
            ]

            tools_used = []
            iteration = 0

            # Tool-calling loop (max 5 iterations)
            while iteration < MAX_ITERATIONS:
                iteration += 1

                # Call Ollama with tools
                response = await self.ollama_client.chat_with_tools(
                    messages=messages,
                    tools=CAREER_TOOLS,
                    stream=False
                )

                # Try to extract tool calls from response
                # Ollama returns tool calls as JSON in content field
                tool_calls_to_process = []

                if response.message.tool_calls:
                    # If tool_calls attribute is populated, use it
                    tool_calls_to_process = response.message.tool_calls
                elif response.message.content:
                    # Try to parse content as a tool call JSON
                    try:
                        parsed = json.loads(response.message.content)
                        if isinstance(parsed, dict) and "name" in parsed and "arguments" in parsed:
                            # This is a tool call in JSON format
                            # Create a fake tool_call object
                            class FakeToolCall:
                                class FakeFunction:
                                    def __init__(self, name, args):
                                        self.name = name
                                        self.arguments = args
                                def __init__(self, name, args):
                                    self.function = self.FakeFunction(name, args)

                            tool_calls_to_process = [FakeToolCall(parsed["name"], parsed.get("arguments", {}))]
                    except (json.JSONDecodeError, TypeError):
                        pass

                # Check if there are any tool calls to process
                if not tool_calls_to_process:
                    # No tool calls — return the final response
                    final_response = response.message.content or ""
                    return {
                        "response": final_response,
                        "tools_used": tools_used,
                        "iterations": iteration
                    }

                # Append assistant message to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.message.content or ""
                })

                # Process each tool call
                tool_results = []
                for tool_call in tool_calls_to_process:
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments or {}

                    try:
                        result = await self.mcp_client.call_tool(tool_name, tool_args)
                        tool_results.append({
                            "tool_name": tool_name,
                            "result": result
                        })
                        if tool_name not in tools_used:
                            tools_used.append(tool_name)
                    except Exception as e:
                        tool_results.append({
                            "tool_name": tool_name,
                            "result": f"Error calling {tool_name}: {str(e)}"
                        })

                # Add tool results as messages
                for tool_result in tool_results:
                    messages.append({
                        "role": "tool",
                        "content": tool_result["result"],
                        "tool_name": tool_result["tool_name"]
                    })

            # Max iterations reached
            return {
                "response": "I've used up my iterations. Please rephrase your question.",
                "tools_used": tools_used,
                "iterations": iteration
            }

        finally:
            if self.mcp_client:
                await self.mcp_client.close()


async def run_career_agent(user_message: str) -> dict:
    """Convenience function to run the agent."""
    agent = CareerAgent()
    return await agent.run(user_message)


# Test function
async def test_agent():
    """Quick test of the agent."""
    print("Testing career agent...")
    result = await run_career_agent("What are Srikanth's AI/ML skills?")
    print(f"\nResponse: {result['response']}")
    print(f"Tools used: {result['tools_used']}")
    print(f"Iterations: {result['iterations']}")


if __name__ == "__main__":
    asyncio.run(test_agent())
