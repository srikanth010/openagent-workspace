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
OpenAgent API (FastAPI, /career/chat)
  - Detects tool usage from message
  - Calls MCP tools
  - Synthesizes response with Ollama
        |
        +--> MCP Server (career/profile data from YAML)
        |
        +--> Ollama (local or remote)
```

---

## System Architecture

### 1. Frontend
- Framework: Next.js (React)
- Uses API endpoint from `NEXT_PUBLIC_CAREER_API_URL`
- Local example: `http://localhost:8000`
- Production example: `https://api.example.com`

### 2. OpenAgent API
- Framework: FastAPI (Python)
- Endpoint: `POST /career/chat`
- Implementation:
  - Keyword-based tool detection
  - MCP subprocess for tool execution
  - Ollama for response synthesis
- Deployment: Railway

### 3. MCP Server
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

### 4. Ollama
- Purpose: Response synthesis
- Local URL: `http://127.0.0.1:11434`
- Model is configurable in API settings

---

## Testing Workflow

### Local Testing

```bash
# Terminal 1
ollama serve

# Terminal 2
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 3 (if using a frontend app)
npm run dev
```

Then test:

```bash
curl -X POST http://127.0.0.1:8000/career/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are my skills?"}'
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

## Vision

OpenAgent Workspace is a learning-focused AI engineering project demonstrating:
- Local-first AI systems with Ollama
- MCP integration
- Production deployment patterns
- API/CORS configuration
- Career-oriented chat automation
