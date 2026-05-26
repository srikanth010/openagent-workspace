# OpenAgent Workspace

Career AI agent infrastructure with MCP, local Ollama, Railway deployment, and Cloudflare tunneling.

**Live:** https://srikanthkanteti.com (Career Chat Widget) | **API:** https://ai.bullminder.com | **Backend:** Railway

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
  -d '{"message":"What are Srikanth skills?"}'
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
┌─────────────────────────────────────────────────────────────────┐
│ User Browser                                                      │
│ https://srikanthkanteti.com (professional-blog)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Chat Widget sends message
                           │ CORS request to API_URL
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Cloudflare (Tunnel)                                               │
│ https://ai.bullminder.com                                        │
│ (Proxies to local Ollama or Railway API)                         │
└──────────────┬──────────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼ (Local Dev)    ▼ (Production)
   localhost:11434      Railway API
   (Ollama)             https://openagent-workspace-production.up.railway.app
       │                │
       └────┬───────────┘
            ▼
    ┌──────────────────────────────────┐
    │ OpenAgent API (FastAPI)          │
    │ POST /career/chat                │
    │ - Detects tools from message     │
    │ - Calls MCP tools (career data)  │
    │ - Synthesizes response (Ollama)  │
    └──────┬─────────────────────────┬─┘
           │                         │
           ▼                         ▼
      MCP Server              Ollama
      (career data:           (qwen35fast:latest)
       skills, projects,      
       experience)            
```

---

## System Architecture

### 1. **Professional Blog** (`/Users/srikanthkanteti/Documents/professional-blog`)
- **Framework:** Next.js (React)
- **Component:** `components/CareerChat/index.tsx`
- **Env Var:** `NEXT_PUBLIC_CAREER_API_URL`
  - **Local:** `http://localhost:8000`
  - **Production:** `https://ai.bullminder.com`
- **Live URL:** https://srikanthkanteti.com

### 2. **OpenAgent API** (`/Users/srikanthkanteti/Documents/openagent-workspace`)
- **Framework:** FastAPI (Python)
- **Endpoint:** `POST /career/chat`
- **Implementation:** 
  - Keyword-based tool detection
  - MCP subprocess for tool execution
  - Ollama for response synthesis
- **Deployment:** Railway (auto-deploy on push)
  - **URL:** https://openagent-workspace-production.up.railway.app
  - **Docker:** Defined in `Dockerfile`
  - **Auto-Deploy:** GitHub integration (push = deploy)

### 3. **MCP Server** (`apps/mcp/career_server.py`)
- **Protocol:** JSON-RPC 2.0 over stdio
- **Tools:**
  - `get_profile` — Srikanth's profile
  - `list_skills` — Skills by category
  - `get_experience` — Work history
  - `get_projects` — Project portfolio
  - `match_to_role` — Fit score for job descriptions
- **Data Source:** YAML files
  - `data/career.yaml`
  - `data/projects.yaml`

### 4. **Ollama** (Local LLM)
- **Model:** `qwen35fast:latest` (4.7B parameters)
- **Purpose:** Response synthesis
- **Local:** `http://127.0.0.1:11434`
- **Remote (via Cloudflare):** `https://ai.bullminder.com`

### 5. **Cloudflare Tunnel** (ai.bullminder.com)
- **Ingress Rule:** Routes `https://ai.bullminder.com` → `localhost:11434` (local dev) or Railway API
- **CORS:** Configured in FastAPI middleware
- **Allowed Origins:**
  - `https://srikanthkanteti.com` (production)
  - `http://localhost:3000` (local dev)
  - `http://localhost:3001` (alternate local port)

---

## Testing Workflow

### Local Testing (Fastest for Development)

**Step 1: Terminal 1 — Start Ollama**
```bash
ollama serve
# Ollama running at http://127.0.0.1:11434
```

**Step 2: Terminal 2 — Start API**
```bash
cd /Users/srikanthkanteti/Documents/openagent-workspace
python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 --reload
# API running at http://127.0.0.1:8000
```

**Step 3: Terminal 3 — Start Blog (if testing widget)**
```bash
cd /Users/srikanthkanteti/Documents/professional-blog
npm run dev
# Blog running at http://localhost:3000
# .env.local has: NEXT_PUBLIC_CAREER_API_URL=http://localhost:8000
```

**Step 4: Test the Chat**
```bash
# Direct API test
curl -X POST http://127.0.0.1:8000/career/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are my skills?"}'

# Or open browser: http://localhost:3000
# Click chat widget, type a question
```

**Expected Response Time:**
- First query: 55-70 seconds (includes model loading into memory)
- Subsequent queries: 10-20 seconds
- Final response is high-quality with proper context

---

### Production Testing (Railway)

**Step 1: Deploy to Railway**
```bash
# Make changes
git add -A
git commit -m "feat: update career agent"
git push origin main

# Railway auto-deploys (watch dashboard)
# Takes ~2-3 minutes
```

**Step 2: Update Blog Config**
```bash
# In /Users/srikanthkanteti/Documents/professional-blog/.env.local
NEXT_PUBLIC_CAREER_API_URL=https://ai.bullminder.com
```

**Step 3: Test Production**
```bash
# API health check
curl https://ai.bullminder.com/health

# Test career chat
curl -X POST https://ai.bullminder.com/career/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What are my skills?"}'

# Open browser: https://srikanthkanteti.com
# Test chat widget
```

---

## Configuration

### Environment Variables

**API Config** (`apps/api/app/core/config.py`):
```python
ollama_base_url = "http://127.0.0.1:11434"  # Local Ollama
career_model = "qwen35fast:latest"
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "https://srikanthkanteti.com"
]
```

**Blog Config** (`professional-blog/.env.local`):
```env
# Local testing
NEXT_PUBLIC_CAREER_API_URL=http://localhost:8000

# Production
NEXT_PUBLIC_CAREER_API_URL=https://ai.bullminder.com
```

**Railway Config** (set in Railway dashboard):
```
OLLAMA_BASE_URL=http://127.0.0.1:11434  (or tunnel URL)
CAREER_MODEL=qwen35fast:latest
ALLOWED_ORIGINS=https://srikanthkanteti.com,http://localhost:3000
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| **Blog chat returns error** | API URL wrong in `.env.local` | Check `NEXT_PUBLIC_CAREER_API_URL` |
| **CORS error in browser** | Origin not in `allowed_origins` | Add domain to FastAPI middleware |
| **API returns 500** | Ollama not running | Start Ollama: `ollama serve` |
| **Slow first response** | Model loading | Normal (55-70s), subsequent queries faster |
| **Railway deployment fails** | Docker build issue | Check `Dockerfile` and `requirements.txt` |

---

## Performance Notes

**Model Loading:**
- First request: ~50-70 seconds (model loads into GPU/memory)
- Subsequent requests: ~10-20 seconds (model stays in memory)
- This is acceptable for a free, local solution

**Alternatives:**
- Use Claude API instead (faster, costs ~$0.001/query)
- Smaller models (qwen2.5:3b) - trade quality for speed

---

## Data Files

Career data is stored in YAML (version controlled):

```
data/
├── career.yaml     # Profile, skills, experience
└── projects.yaml   # Project portfolio
```

Update these files to change career data. Changes are:
1. Reflected in local API immediately
2. Deployed to Railway on next `git push`

---

## Next Steps

1. ✅ **Verify local setup works** — Run through "Local Testing" section
2. ✅ **Test blog widget locally** — Open http://localhost:3000
3. ✅ **Deploy to Railway** — `git push origin main`
4. ✅ **Update blog for production** — Set API URL to `https://ai.bullminder.com`
5. **Monitor Railway logs** — Check https://railway.app for errors
6. **Share blog link** — Portfolio is now live with AI career chat!

---

## Links

- **Live Blog:** https://srikanthkanteti.com
- **Live API:** https://ai.bullminder.com
- **Railway Dashboard:** https://railway.app
- **GitHub Repo:** https://github.com/srikanth010/openagent-workspace
- **Blog Repo:** `/Users/srikanthkanteti/Documents/professional-blog`

---

## Vision

OpenAgent Workspace is a learning-focused AI engineering project that demonstrates:
- Local-first AI systems with Ollama
- MCP (Model Context Protocol) integration
- Production deployment on Railway
- CORS handling and API security
- Career portfolio with AI automation

The goal is to learn real-world AI infrastructure while building a public engineering portfolio that showcases skills to potential employers (Anthropic, OpenAI, Google, NVIDIA).