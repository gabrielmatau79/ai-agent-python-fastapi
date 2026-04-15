from __future__ import annotations

import json
from typing import Any

from app.core.exceptions import ConfigurationError


def parse_json_string(
    raw: str, *, expect: type[list[Any]] | type[dict[str, Any]], label: str
) -> Any:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"{label} contains invalid JSON: {exc.msg}") from exc
    if not isinstance(value, expect):
        expected = "array" if expect is list else "object"
        raise ConfigurationError(f"{label} must be a JSON {expected}.")
    return value
