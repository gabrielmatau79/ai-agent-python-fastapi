# Usage

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp docs/env-examples/.env.example .env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- `http://localhost:8000/docs`
- `http://localhost:8000/openapi.json`

## Example Request

```bash
curl -X POST http://localhost:8000/api/v1/agent/ask \
  -H "Content-Type: application/json" \
  -d '{
    "userInput": "What is Kubernetes?",
    "sessionId": "session-abc123",
    "userLang": "en"
  }'
```

## Local MCP Server

Run the local MCP server over stdio:

```bash
python -m app.mcp_server.server
```

To enable it for the main app:

```env
MCP_SERVERS={"localAgent":{"transport":"stdio","command":"python","args":["-m","app.mcp_server.server"],"optional":true}}
```

## Docker

```bash
cp docs/env-examples/.env.docker.example .env
docker compose up --build
```
