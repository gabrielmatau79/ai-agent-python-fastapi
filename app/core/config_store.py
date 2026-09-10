from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from app.core.exceptions import ConfigurationError
from app.core.settings import Settings


def load_overrides(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"{path} contains invalid JSON: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise ConfigurationError(f"{path} must contain a JSON object.")
    return raw


def save_overrides(path: Path, overrides: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(overrides, indent=2, sort_keys=True), encoding="utf-8")
    os.chmod(tmp_path, 0o600)
    os.replace(tmp_path, path)


def merge_overrides(existing: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in patch.items():
        if value is None:
            merged.pop(key, None)
        else:
            merged[key] = value
    return merged


def build_settings(overrides_path: Path | None = None) -> Settings:
    base = Settings()
    path = overrides_path or base.runtime_config_path
    overrides = load_overrides(path)
    if not overrides:
        return base
    return Settings(**overrides)
