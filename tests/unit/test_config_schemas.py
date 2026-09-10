from app.core.settings import Settings
from app.schemas.config import to_editable_sections


def test_to_editable_sections_never_leaks_raw_secrets() -> None:
    settings = Settings(
        openai_api_key="sk-super-secret",
        anthropic_api_key="anthropic-secret",
        llm_tools_auth_token="tools-secret",
        mcp_auth_token="mcp-secret",
    )
    sections = to_editable_sections(settings)
    payload = sections.model_dump_json()

    assert "sk-super-secret" not in payload
    assert "anthropic-secret" not in payload
    assert "tools-secret" not in payload
    assert "mcp-secret" not in payload
    assert sections.llm.openai_api_key_set is True
    assert sections.llm.anthropic_api_key_set is True
    assert sections.tools.llm_tools_auth_token_set is True
    assert sections.mcp.mcp_auth_token_set is True


def test_to_editable_sections_reports_unset_secrets() -> None:
    settings = Settings(
        openai_api_key=None,
        anthropic_api_key=None,
        llm_tools_auth_token=None,
        mcp_auth_token=None,
    )
    sections = to_editable_sections(settings)
    assert sections.llm.openai_api_key_set is False
    assert sections.llm.anthropic_api_key_set is False
    assert sections.tools.llm_tools_auth_token_set is False
    assert sections.mcp.mcp_auth_token_set is False


def test_to_editable_sections_exposes_non_secret_values() -> None:
    settings = Settings(agent_prompt="Custom prompt", rag_top_k=7)
    sections = to_editable_sections(settings)
    assert sections.agent.agent_prompt == "Custom prompt"
    assert sections.rag.rag_top_k == 7
