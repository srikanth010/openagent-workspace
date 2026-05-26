# Deployment Guide

This guide covers deploying the Career Agent Backend to Railway.

## Prerequisites

- [Railway CLI](https://docs.railway.app/guides/cli) installed
- GitHub repository connected to Railway
- Domain for CORS configuration (e.g., srikanthkanteti.com)

## Quick Start (Railway)

### 1. Login to Railway

```bash
railway login
```

### 2. Initialize Railway Project

```bash
railway init
```

Follow the prompts to create a new project.

### 3. Configure Environment Variables

Set these in the Railway dashboard or via CLI:

```bash
railway variable set OLLAMA_BASE_URL=https://ai.bullminder.com
railway variable set OLLAMA_MODEL=qwen2.5:7b
railway variable set CAREER_MODEL=qwen2.5:7b
railway variable set ALLOWED_ORIGINS=https://srikanthkanteti.com,http://localhost:3000
```

### 4. Deploy

```bash
railway up
```

This will:
1. Build the Docker image
2. Push to Railway
3. Deploy the application
4. Assign a public URL

### 5. Get Your URL

```bash
railway domain
```

This outputs your public deployment URL. Update your Next.js `.env.local`:

```env
NEXT_PUBLIC_CAREER_API_URL=https://your-railway-url.app
```

## Model Selection

### For Local Development
- **Model:** `qwen2.5-coder:32b`
- **RAM:** ~20GB
- **Speed:** Slow on MacBook, good quality

### For Railway Deployment
- **Model:** `qwen2.5:7b`
- **RAM:** ~7GB (fits in Railway's standard container)
- **Speed:** Faster, still good quality
- **Command:** Set `CAREER_MODEL=qwen2.5:7b` in Railway

## Local Ollama Setup (for testing before deploy)

### Install Ollama

```bash
# Download from https://ollama.ai
# Or via Homebrew:
brew install ollama
```

### Start Ollama

```bash
ollama serve
```

### Pull Models

```bash
# For development (high quality, slower)
ollama pull qwen2.5-coder:32b

# For production testing (smaller, faster)
ollama pull qwen2.5:7b
```

## Testing After Deploy

### Health Check

```bash
curl https://your-railway-url.app/health
```

### Test Career Chat

```bash
curl -X POST https://your-railway-url.app/career/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are your AI skills?"}'
```

### Test CORS

```bash
curl -X OPTIONS https://your-railway-url.app/career/chat \
  -H "Origin: https://srikanthkanteti.com" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

Should return `access-control-allow-origin: https://srikanthkanteti.com` in response headers.

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama server URL | `https://ai.bullminder.com` |
| `OLLAMA_MODEL` | Default Ollama model | `qwen2.5:7b` |
| `CAREER_MODEL` | Model for career agent | `qwen2.5:7b` |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | `https://srikanthkanteti.com` |

## Troubleshooting

### 504 Gateway Timeout
- Increase Railway's timeout settings
- The first request with a new model takes time to load
- Consider using a smaller model like `qwen2.5:7b`

### CORS Errors in Browser
- Check `ALLOWED_ORIGINS` includes your domain
- Restart the Railway deployment after changing env vars
- Verify the domain in your Next.js `.env.local`

### Model Not Loading
- Verify Ollama is running: `curl https://ai.bullminder.com/api/tags`
- Check the model is pulled: `ollama list`
- View logs: `railway logs`

## Local vs Production Model

| Aspect | Local | Production |
|--------|-------|-----------|
| Model | `qwen2.5-coder:32b` | `qwen2.5:7b` |
| Memory | ~20GB | ~7GB |
| Speed | Slower | Faster |
| Quality | Higher | Good |
| Cost | Free | Railway dynos |

To match production locally:

```bash
# Set model in .env or export:
export CAREER_MODEL=qwen2.5:7b
# Pull the model
ollama pull qwen2.5:7b
# Test locally
python -c "import asyncio; from apps.api.app.agents.career_agent import run_career_agent; asyncio.run(run_career_agent('Test'))"
```

## CI/CD Pipeline

Railway automatically deploys on `git push` if your GitHub repo is connected. To set this up:

1. Go to Railway dashboard
2. Click "Settings"
3. Connect your GitHub repository
4. Enable "Auto Deploy on Push"

## Next Steps

1. Deploy to Railway (this guide)
2. Update your Next.js site's `.env.local` with the Railway URL
3. Test the chat widget on your live site
4. Write a blog post about the architecture
5. Apply to jobs with your working demo!
