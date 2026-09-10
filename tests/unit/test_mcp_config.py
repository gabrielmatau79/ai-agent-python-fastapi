import pytest

from app.core.exceptions import ConfigurationError
from app.core.settings import Settings


def test_mcp_config_parsing() -> None:
    settings = Settings(
        mcp_servers='{"remote":{"transport":"streamable_http","url":"http://localhost:9000/mcp","optional":true}}'
    )
    assert settings.parsed_mcp_servers["remote"].url == "http://localhost:9000/mcp"


def test_mcp_invalid_json_raises() -> None:
    settings = Settings(mcp_servers="{invalid}")
    with pytest.raises(ConfigurationError):
        _ = settings.parsed_mcp_servers
