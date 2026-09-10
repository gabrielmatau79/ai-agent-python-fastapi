from pathlib import Path

import pytest

from app.core.config_store import (
    build_settings,
    load_overrides,
    merge_overrides,
    save_overrides,
)
from app.core.exceptions import ConfigurationError


def test_load_overrides_missing_file_returns_empty(tmp_path: Path) -> None:
    assert load_overrides(tmp_path / "missing.json") == {}


def test_save_and_load_overrides_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "overrides.json"
    save_overrides(path, {"agent_prompt": "hello"})
    assert load_overrides(path) == {"agent_prompt": "hello"}


def test_load_overrides_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "overrides.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_overrides(path)


def test_load_overrides_rejects_non_object_json(tmp_path: Path) -> None:
    path = tmp_path / "overrides.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_overrides(path)


def test_merge_overrides_null_clears_key() -> None:
    existing = {"agent_prompt": "old", "llm_model": "gpt-4o-mini"}
    patch = {"agent_prompt": None, "llm_temperature": 0.5}
    merged = merge_overrides(existing, patch)
    assert merged == {"llm_model": "gpt-4o-mini", "llm_temperature": 0.5}


def test_merge_overrides_absent_key_untouched() -> None:
    existing = {"agent_prompt": "old"}
    merged = merge_overrides(existing, {})
    assert merged == {"agent_prompt": "old"}


def test_build_settings_without_overrides_file_uses_defaults(tmp_path: Path) -> None:
    settings = build_settings(tmp_path / "missing.json")
    assert settings.agent_prompt.startswith("You are a helpful AI assistant")


def test_build_settings_applies_overrides(tmp_path: Path) -> None:
    path = tmp_path / "overrides.json"
    save_overrides(path, {"agent_prompt": "Custom prompt"})
    settings = build_settings(path)
    assert settings.agent_prompt == "Custom prompt"
