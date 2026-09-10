# Environment Variables

Example environment presets are stored in:

- `docs/env-examples/.env.example`
- `docs/env-examples/.env.openai.example`
- `docs/env-examples/.env.ollama.example`
- `docs/env-examples/.env.anthropic.example`
- `docs/env-examples/.env.docker.example`

Copy the one you want into the project root as `.env` before starting the app.

## App

| Variable | Description |
| --- | --- |
| `APP_NAME` | FastAPI application title. |
| `APP_ENV` | Environment label such as `development`, `docker`, or `production`. |
| `APP_PORT` | Application port. |
| `LOG_LEVEL` | Standard Python log level such as `INFO` or `DEBUG`. |
| `API_V1_PREFIX` | Base prefix for versioned API routes. |
| `CORS_ALLOW_ORIGINS` | JSON array or comma-separated origin list. |

## Agent

| Variable | Description |
| --- | --- |
| `AGENT_PROMPT` | Base system instruction. |
| `DEFAULT_RESPONSE_LANGUAGE` | Fallback response language code. |
| `LANGUAGE_DETECTION_ENABLED` | Enables language detection when `userLang` is absent. |

## LLM

| Variable | Description |
| --- | --- |
| `LLM_PROVIDER` | `openai`, `ollama`, or `anthropic`. |
| `LLM_MODEL` | Generic fallback model name. |
| `LLM_TEMPERATURE` | Generation temperature. |
| `LLM_MAX_TOKENS` | Maximum output tokens. |
| `LLM_TIMEOUT_SECONDS` | LLM and HTTP timeout. |

## Provider-Specific

| Variable | Description |
| --- | --- |
| `OPENAI_API_KEY` | API key for OpenAI requests. |
| `OPENAI_MODEL` | OpenAI chat model name. |
| `OLLAMA_BASE_URL` | Base URL for the Ollama server. |
| `OLLAMA_MODEL` | Ollama model name. |
| `ANTHROPIC_API_KEY` | API key for Anthropic requests. |
| `ANTHROPIC_MODEL` | Anthropic model name. |

## Memory

| Variable | Description |
| --- | --- |
| `AGENT_MEMORY_TYPE` | `memory` or `redis`. |
| `AGENT_MEMORY_WINDOW` | Max stored messages per session. |
| `MEMORY_TTL_SECONDS` | Redis memory TTL. |
| `REDIS_URL` | Shared Redis connection URL. |

## RAG

| Variable | Description |
| --- | --- |
| `RAG_PROVIDER` | `in_memory` or `redis`. |
| `RAG_DOCS_PATH` | Directory scanned for `.txt`, `.md`, `.csv`, and `.pdf`. |
| `RAG_TOP_K` | Retrieval count. |
| `RAG_CHUNK_SIZE` | Chunk size. |
| `RAG_CHUNK_OVERLAP` | Chunk overlap. |
| `EMBEDDING_PROVIDER` | `local` or `openai`. |
| `EMBEDDING_MODEL` | Embedding model name when OpenAI embeddings are used. |
| `VECTOR_STORE` | Descriptive backend label. |
| `VECTOR_INDEX_NAME` | Redis hash namespace. |

## Tools

| Variable | Description |
| --- | --- |
| `LLM_TOOLS_CONFIG` | JSON array of HTTP tool definitions. |
| `LLM_TOOLS_AUTH_TOKEN` | Optional token for authenticated HTTP tools. |
| `LLM_TOOLS_AUTH_HEADER` | Header name used for tool authentication. |
| `LLM_TOOLS_AUTH_SCHEME` | Auth scheme prefix such as `Bearer`. |

## MCP

| Variable | Description |
| --- | --- |
| `MCP_SERVERS` | JSON object keyed by server name. |
| `MCP_TOOL_TIMEOUT_MS` | Timeout for MCP tool calls in milliseconds. |
| `MCP_THROW_ON_LOAD_ERROR` | Whether MCP loading errors should fail startup. |
| `MCP_USE_STANDARD_CONTENT_BLOCKS` | Normalize MCP content blocks for downstream usage. |
| `MCP_AUTH_TOKEN` | Default auth token for MCP HTTP transports. |
| `MCP_AUTH_HEADER` | Header name used with `MCP_AUTH_TOKEN`. |

Example:

```env
MCP_SERVERS={"localAgent":{"transport":"stdio","command":"python","args":["-m","app.mcp_server.server"],"optional":true}}
```

## Security

| Variable | Description |
| --- | --- |
| `API_KEY_ENABLED` | Enables API key protection for protected endpoints. |
| `API_KEY_HEADER_NAME` | Header name expected for the API key. |
| `API_KEY_VALUE` | Secret API key value. |

Secrets are redacted from logs and from `GET /api/v1/config/effective-sanitized`.

## Runtime config

| Variable | Description |
| --- | --- |
| `RUNTIME_CONFIG_PATH` | Path to the JSON file holding admin-UI overrides applied on top of `.env`. Defaults to `config/runtime-overrides.json`. |

See [docs/admin-ui.md](./admin-ui.md) for how the admin UI at `/admin/` uses
this file to apply configuration changes without restarting the app.
