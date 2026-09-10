# Architecture

## Diagram

Rendered architecture diagram:

![AI Agent FastAPI Architecture](./assets/ia_agent_fastapipng)

Source PlantUML:

- [architecture.puml](./assets/architecture.puml)

The application is organized around a service-oriented architecture with clear provider boundaries:

- `AgentService` orchestrates language selection, session history loading, RAG retrieval, prompt construction, LLM invocation, and message persistence.
- `MemoryService` sits on top of interchangeable backends:
  - `InMemoryMemoryProvider`
  - `RedisMemoryProvider`
- `RagService` sits on top of interchangeable backends:
  - `InMemoryRagProvider`
  - `RedisRagProvider`
- `LlmService` delegates to one provider selected by configuration:
  - OpenAI
  - Ollama
  - Anthropic
- `ToolsService` exposes built-in and environment-driven HTTP tools.
- `McpClientService` connects to multiple MCP servers and turns discovered tools into LangChain-compatible tools.
- `app.mcp_server.server` exposes local MCP tools backed by the same RAG and memory contracts.

## Request Flow

1. `POST /api/v1/agent/ask` validates the request body.
2. Language is taken from `userLang` or detected with a deterministic heuristic fallback.
3. Session memory is loaded.
4. RAG retrieves top-k chunks from indexed documents.
5. Prompt utilities build structured chat messages with explicit history and retrieved context blocks.
6. The configured LLM provider generates the answer, optionally with tool calling.
7. User and assistant messages are written back to memory.

## Lifespan Management

FastAPI lifespan initializes and closes:

- logging
- selected memory backend
- selected RAG backend
- MCP client connections
- HTTP tooling client

## RAG Notes

The RAG layer supports both in-memory and Redis-backed implementations behind the same abstraction. The Redis-backed option uses a production-safe document storage approach with application-side similarity scoring, which keeps the setup portable and reliable without requiring Redis Stack.
