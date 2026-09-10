from app.llm.factory import supports_tools_by_provider


def test_supports_tools_by_provider_matches_provider_capabilities() -> None:
    assert supports_tools_by_provider() == {
        "openai": True,
        "ollama": False,
        "anthropic": True,
    }
