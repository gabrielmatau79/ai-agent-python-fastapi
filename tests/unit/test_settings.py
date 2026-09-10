from app.core.settings import Settings


def test_settings_parse_lists_and_json() -> None:
    settings = Settings(
        cors_allow_origins='["http://localhost:3000"]',
        llm_tools_config='[{"name":"toolA","description":"desc","endpoint":"https://example.com/{query}","method":"GET","requiresAuth":false}]',
        mcp_servers='{"local":{"transport":"stdio","command":"python","args":["-m","app.mcp_server.server"],"optional":true}}',
    )
    assert settings.cors_allow_origins == ["http://localhost:3000"]
    assert settings.parsed_http_tools[0].name == "toolA"
    assert settings.parsed_mcp_servers["local"].command == "python"
