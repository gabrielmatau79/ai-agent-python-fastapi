# AI Agent FastAPI

Production-grade AI agent platform built with FastAPI, designed around async-first services, configurable LLM providers, RAG, session memory, MCP integration, and production-oriented operational tooling.

## Features

- REST API for agent interaction
- Session memory with in-memory and Redis backends
- RAG with in-memory and Redis-backed providers
- OpenAI, Ollama, and Anthropic LLM support
- Dynamic HTTP tools from environment JSON
- MCP client support for multiple servers and transports
- Local MCP server exposing memory and RAG tools
- OpenAPI and Swagger docs
- Docker and Docker Compose
- Unit and integration tests

## Architecture Summary

- [docs/architecture.md](/home/gabrielmatau/Documentos/desarrollos/ai-agent-python-fastapi/docs/architecture.md)
- [docs/env.md](/home/gabrielmatau/Documentos/desarrollos/ai-agent-python-fastapi/docs/env.md)
- [docs/usage.md](/home/gabrielmatau/Documentos/desarrollos/ai-agent-python-fastapi/docs/usage.md)

## Endpoints

- `POST /api/v1/agent/ask`
- `GET /health/live`
- `GET /health/ready`
- `GET /api/v1/memory/{session_id}`
- `DELETE /api/v1/memory/{session_id}`
- `POST /api/v1/rag/reindex`
- `GET /api/v1/config/effective-sanitized`

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp docs/env-examples/.env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## LLM Configuration

### OpenAI

```bash
cp docs/env-examples/.env.openai.example .env
```

Set `OPENAI_API_KEY`.

### Ollama

```bash
cp docs/env-examples/.env.ollama.example .env
```

Make sure Ollama is running and the configured model is pulled.

### Anthropic

```bash
cp docs/env-examples/.env.anthropic.example .env
```

Set `ANTHROPIC_API_KEY`.

## Memory Configuration

- `AGENT_MEMORY_TYPE=memory` for local development
- `AGENT_MEMORY_TYPE=redis` for shared or persistent sessions

## RAG Configuration

Point `RAG_DOCS_PATH` to a folder containing `.txt`, `.md`, `.csv`, or `.pdf` files. Sample documents are included in `sample_docs/` so the app works immediately.

## HTTP Tools Configuration

```env
LLM_TOOLS_CONFIG='[
  {
    "name": "getZipInfo",
    "description": "Get zip code information",
    "endpoint": "https://api.zippopotam.us/us/{query}",
    "method": "GET",
    "requiresAuth": false
  }
]'
```

Rules implemented:

- `{query}` placeholders are URL-encoded and replaced
- GET requests without placeholders append `?q=<input>`
- non-GET requests send `{"query": "<input>"}` JSON bodies
- auth headers are injected when `requiresAuth=true`

## MCP Client Configuration

```env
MCP_SERVERS={"localAgent":{"transport":"stdio","command":"python","args":["-m","app.mcp_server.server"],"optional":true}}
```

Supported transports:

- `stdio`
- `streamable_http`
- `sse`

## Local MCP Server Usage

```bash
python -m app.mcp_server.server
```

Exposed tools:

- `query_rag`
- `get_memory_history`
- `add_memory_message`
- `clear_memory`

## Example API Request

```bash
curl -X POST http://localhost:8000/api/v1/agent/ask \
  -H "Content-Type: application/json" \
  -d '{
    "userInput": "What is Kubernetes?",
    "sessionId": "session-abc123",
    "userLang": "en"
  }'
```

## Test, Lint, Type Check

```bash
pytest
ruff check .
mypy app
```

Typos check:

```bash
typos
```

## Docker

```bash
cp docs/env-examples/.env.docker.example .env
docker compose up --build
```

## CI

GitHub Actions now validates:

- `ruff check .`
- `mypy app`
- `pytest -q`
- `typos`

## Troubleshooting

- If `LLM_PROVIDER=openai`, set `OPENAI_API_KEY`.
- If `LLM_PROVIDER=anthropic`, set `ANTHROPIC_API_KEY`.
- If `LLM_PROVIDER=ollama`, make sure Ollama is reachable at `OLLAMA_BASE_URL`.
- If Redis-backed memory or RAG is enabled, make sure `REDIS_URL` is reachable.
- If optional MCP servers fail to connect, the app logs a warning and continues.
