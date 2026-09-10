from __future__ import annotations

from fastapi.security import APIKeyHeader


def api_key_header(name: str) -> APIKeyHeader:
    return APIKeyHeader(name=name, auto_error=False)
