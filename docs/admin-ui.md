# Admin UI

A server-rendered admin page at `GET /admin/` lets an operator edit LLM, agent,
memory, RAG, tools, and MCP settings while the app is running, with no restart
required.

## Access

- If `API_KEY_ENABLED=false` (the default), `/admin/` is open, same as the
  rest of the API today.
- If `API_KEY_ENABLED=true`, open `/admin/?key=<API_KEY_VALUE>` once. The page
  injects that key into every subsequent HTMX request via `hx-headers`, so no
  session/cookie mechanism is needed.

## How changes take effect

Each section is its own form. Saving a section calls the same
`ConfigService.apply_patch()` used by `PATCH /api/v1/config`, which:

1. Validates the merged configuration (current overrides + your patch) against
   the same pydantic models used everywhere else in the app.
2. Rebuilds only the services affected by the fields you changed (see the
   table in the architecture notes) and swaps them into the running
   container.
3. Persists the change to `config/runtime-overrides.json` so it survives a
   restart. Precedence: `Settings` defaults < `.env`/env vars <
   `config/runtime-overrides.json`.

## Known limitations

- **Secrets on disk**: once you set an API key or auth token from the admin
  UI, it is written to `config/runtime-overrides.json` (mode `0600`,
  git-ignored). The UI never displays a previously-set secret back to you —
  only whether one is configured.
- **Multi-process/multi-worker deployments**: a saved change only updates the
  process that received the write. This mirrors the existing limitation of
  `AGENT_MEMORY_TYPE=memory` (in-process state), and isn't solved by this
  feature.
- **Switching memory backend** (`AGENT_MEMORY_TYPE`) drops any session
  history held by the previous backend — the UI asks for confirmation before
  submitting that change.
- **RAG/embedding changes trigger a full reindex** of `RAG_DOCS_PATH`, which
  can be slow for large document sets.
