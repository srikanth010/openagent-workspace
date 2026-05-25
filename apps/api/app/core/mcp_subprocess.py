"""
MCP Subprocess Manager
Manages the lifecycle of the MCP server running as a subprocess.
Handles JSON-RPC 2.0 communication over stdio.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Any

# Path to MCP server script
# From: apps/api/app/core/mcp_subprocess.py
# To: apps/mcp/career_server.py
MCP_SERVER_PATH = Path(__file__).parent.parent.parent.parent / "mcp" / "career_server.py"


class MCPClient:
    """Manages MCP server subprocess and JSON-RPC communication."""

    def __init__(self, timeout_seconds: int = 10):
        self.process: Optional[asyncio.subprocess.Process] = None
        self.timeout_seconds = timeout_seconds
        self._message_id = 0

    async def start(self) -> None:
        """Start the MCP server subprocess and perform handshake."""
        if self.process is not None:
            return

        try:
            self.process = await asyncio.create_subprocess_exec(
                "python",
                str(MCP_SERVER_PATH),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Give subprocess time to start and load data
            await asyncio.sleep(0.1)

            # Perform initialize handshake
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "clientInfo": {
                        "name": "career-agent",
                        "version": "1.0.0"
                    }
                }
            }

            self.process.stdin.write((json.dumps(init_msg) + "\n").encode())
            await self.process.stdin.drain()

            # Read initialize response with timeout
            try:
                response_line = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                raise RuntimeError("MCP server did not respond to initialize")

            if not response_line:
                raise RuntimeError("MCP server closed connection during initialize")

            try:
                response = json.loads(response_line.decode())
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Failed to parse initialize response: {e}")

            if "error" in response:
                raise RuntimeError(f"Initialize failed: {response.get('error')}")

            # Send initialized notification
            notif_msg = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            }
            self.process.stdin.write((json.dumps(notif_msg) + "\n").encode())
            await self.process.stdin.drain()

        except Exception as e:
            if self.process:
                try:
                    self.process.kill()
                except:
                    pass
                self.process = None
            raise RuntimeError(f"Failed to start MCP server: {e}")

    async def close(self) -> None:
        """Close the subprocess."""
        if self.process:
            self.process.stdin.close()
            try:
                await self.process.wait()
            except:
                pass
            self.process = None

    async def call_tool(self, name: str, arguments: dict) -> str:
        """
        Call an MCP tool and return the result as a string.

        Args:
            name: Tool name
            arguments: Tool arguments as dict

        Returns:
            Tool result as JSON string
        """
        if not self.process:
            raise RuntimeError("MCP client not started")

        self._message_id += 1
        message = {
            "jsonrpc": "2.0",
            "id": self._message_id,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }

        self.process.stdin.write((json.dumps(message) + "\n").encode())
        await self.process.stdin.drain()

        try:
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"Tool call {name} timed out after {self.timeout_seconds}s")

        if not response_line:
            raise RuntimeError(f"MCP server closed connection during tool call {name}")

        try:
            response = json.loads(response_line.decode())
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse tool response: {e}")

        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"Tool error: {error.get('message', error)}")

        result = response.get("result", {})
        content = result.get("content", [])

        if content and len(content) > 0:
            return content[0].get("text", "")

        return ""


async def test_mcp_connection():
    """Quick test to verify MCP server works."""
    client = MCPClient()
    try:
        await client.start()
        result = await client.call_tool("get_profile", {})
        print("✓ MCP connection successful")
        print(f"Profile: {result[:100]}...")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
