# OpenAgent Workspace

Local-first AI agent infrastructure platform with MCP, Skills, Ollama, RAG, and observability.

---

## Vision

OpenAgent Workspace is a learning-focused AI engineering project designed to explore how modern AI systems are built locally using:

- Local LLMs
- MCP (Model Context Protocol)
- AI Skills
- Agent workflows
- Tool calling
- RAG pipelines
- Observability
- Multi-model orchestration

The goal of this project is to learn and build production-style AI systems step-by-step while maintaining a strong public engineering portfolio.

---

# Project Goals

This project focuses on:

- Understanding AI agent architectures
- Building reusable AI Skills
- Creating MCP-compatible tools and servers
- Running local-first AI systems with Ollama
- Building observability for AI workflows
- Learning real-world AI infrastructure patterns
- Documenting the engineering journey publicly

---

# Core Features (Planned)

## Local LLM Runtime
- Ollama integration
- Local model routing
- Multi-model support

## MCP Server
- Filesystem tools
- Repo analysis tools
- Search tools
- Documentation tools

## Skills System
Reusable AI Skills such as:
- Repo summarization
- Architecture generation
- Documentation generation
- Incident analysis
- Release notes generation

## Agent Runtime
- Tool calling
- Workflow execution
- Multi-step reasoning
- Memory support

## RAG Pipeline
- Local document ingestion
- Semantic search
- Vector embeddings
- Context retrieval

## Observability
- AI traces
- Tool call tracking
- Latency monitoring
- Token usage tracking
- Workflow debugging

---

# Tech Stack

## Backend
- Python
- FastAPI
- asyncio
- Pydantic

## Frontend (Planned)
- Next.js
- TailwindCSS

## AI Stack
- Ollama
- Local LLMs
- MCP
- RAG pipelines

## Observability (Planned)
- OpenTelemetry
- Langfuse
- Jaeger

---

# Project Structure

```txt
openagent-workspace/
├── apps/
│   ├── api/
│   └── cli/
│
├── packages/
│
├── docs/
│
├── examples/
│
├── scripts/
│
├── tests/
│
├── requirements.txt
└── README.md