# OpenAgent Workspace

Career AI agent infrastructure with MCP, local Ollama, Railway deployment, and optional Cloudflare tunneling.

---

## Quick Start

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama (in another terminal)
ollama serve

# 3. Start the API
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 --reload

# 4. Test the API
curl -X POST http://127.0.0.1:8000/career/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are my skills?"}'
```

### Deploy to Railway

```bash
git add -A && git commit -m "your message"
git push origin main
# Railway auto-deploys on push
```

---

## Architecture Overview

```
User Browser (chat widget)
        |
        v
Cloudflare Tunnel or direct API URL
        |
        v
OpenAgent API (FastAPI)
  - /career/chat (REST, non-streaming)
  - /career/ws (WebSocket, streaming with session memory)
        |
        +---> Tool Detection + MCP Server (YAML data)
        |
        +---> Ollama (token-by-token streaming)
        |
        +---> Session Store (conversation history)
```

---

## System Architecture

### 1. Frontend
- Framework: Next.js (React)
- Uses WebSocket endpoint from `NEXT_PUBLIC_CAREER_API_URL`
- Local example: `ws://localhost:8000`
- Production example: `wss://api.example.com`

### 2. OpenAgent API
- Framework: FastAPI (Python)
- Endpoints:
  - `POST /career/chat` — REST endpoint (non-streaming, backwards compatible)
  - `GET /career/ws` — WebSocket endpoint (streaming tokens, multi-turn memory)
- Implementation:
  - Keyword-based tool detection
  - MCP subprocess for tool execution
  - Ollama for response synthesis
  - In-memory session store for conversation history
- Deployment: Railway

### 3. Session Management
- In-memory store: `apps/api/app/core/session_store.py`
- Tracks conversation history per session_id
- Auto-expires sessions after 30 minutes of inactivity
- Resets on server restart (acceptable for blog demo)

### 4. Streaming Response
- WebSocket protocol: `/career/ws`
- Client sends: `{"message": "...", "session_id": "..."}`
- Server streams: `{"token": "..."}` then `{"done": true, "tools_used": [...]}`
- Tokens arrive character-by-character for real-time feedback

### 5. MCP Server
- Path: `apps/mcp/career_server.py`
- Protocol: JSON-RPC 2.0 over stdio
- Tools:
  - `get_profile`
  - `list_skills`
  - `get_experience`
  - `get_projects`
  - `match_to_role`
- Data Source:
  - `data/career.yaml`
  - `data/projects.yaml`

### 6. Ollama
- Purpose: Response synthesis
- Local URL: `http://127.0.0.1:11434`
- Model is configurable in API settings
- Supports streaming for token-by-token output

---

## API Endpoints

### REST (Non-streaming)
```
POST /career/chat
Content-Type: application/json

{
  "message": "What are your skills?",
  "session_id": "optional-uuid"
}

Response:
{
  "response": "...",
  "tools_used": ["list_skills"],
  "iterations": 1,
  "response_time_ms": 2500,
  "context_preview": "..."
}
```

### WebSocket (Streaming, Recommended)
```
WS /career/ws

Client sends:
{"message": "What are your skills?", "session_id": "recruiter-123"}

Server streams:
{"token": "Srikanth"}
{"token": " has"}
{"token": " expertise"}
...
{"done": true, "tools_used": ["list_skills"], "session_id": "recruiter-123"}
```

---

## Testing Workflow

### Local Testing

```bash
# Terminal 1
ollama serve

# Terminal 2
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 3 (if using a frontend app)
cd /path/to/professional-blog
npm run dev
```

### Test REST Endpoint

```bash
curl -X POST http://127.0.0.1:8000/career/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are my skills?"}'
```

### Test WebSocket Streaming

```bash
python3 << 'EOF'
import asyncio
import json
import websockets

async def test():
    async with websockets.connect('ws://127.0.0.1:8000/career/ws') as ws:
        await ws.send(json.dumps({
            'message': 'Tell me about your experience',
            'session_id': 'test-1'
        }))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if 'token' in data:
                print(data['token'], end='', flush=True)
            elif data.get('done'):
                print('\n✓ Done')
                break

asyncio.run(test())
EOF
```

### Production Testing

```bash
# Deploy
git add -A
git commit -m "feat: update career agent"
git push origin main

# Health check
curl https://api.example.com/health

# Chat endpoint
curl -X POST https://api.example.com/career/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are my skills?"}'
```

---

## Configuration

### Environment Variables

API settings (see `apps/api/app/core/config.py`):

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5-coder:7b
CAREER_MODEL=qwen2.5-coder:7b
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:3001"]
```

Frontend settings:

```env
NEXT_PUBLIC_CAREER_API_URL=http://localhost:8000
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Chat returns error | API URL mismatch | Check `NEXT_PUBLIC_CAREER_API_URL` |
| CORS error in browser | Origin not allowed | Add origin to `allowed_origins` |
| API returns 500 | Ollama not running | Start Ollama with `ollama serve` |
| Slow first response | Model warm-up | First request can be slower |

---

## Data Files

Career data is stored in YAML:

```
data/
├── career.yaml
└── projects.yaml
```

Update these files to change profile/career content served by MCP tools.

---

## Session Management

Conversation history is stored in-memory per session:

```python
# Each session stores:
{
  "session_id": "uuid-here",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    ...
  ],
  "last_active": 1234567890,
}
```

**Storage**: In-memory Python dict
- **Lifetime**: Sessions auto-expire after 30 minutes (configurable via `evict_stale()`)
- **Restart**: Sessions are lost when server restarts (acceptable for blog demo)
- **Persistence**: For production, migrate to SQLite via `apps/api/app/core/session_store.py`

**Conversation Context**: 
- History is capped at 10 prior messages (5 turns) to stay within Ollama's context window
- Each turn includes the full conversation history + fresh MCP tool data for the current question
- Older messages are dropped when the cap is exceeded

---

## Vision

OpenAgent Workspace is a learning-focused AI engineering project demonstrating:
- Local-first AI systems with Ollama
- MCP integration
- Production deployment patterns
- API/CORS configuration
- Career-oriented chat automation
- **Real-time token streaming** via WebSocket
- **Conversation memory** with session-based history
- Multi-turn AI chat with context awareness
