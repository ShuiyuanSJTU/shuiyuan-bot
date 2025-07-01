import pytest
from unittest.mock import mock_open, patch


@pytest.fixture
def mock_config_file():
    config_content = """
    site_url: "http://example.com"
    bind_address: "127.0.0.1"
    bind_port: 8080
    redis_host: "localhost"
    redis_port: 6379
    server:
        bind_address: "127.0.0.1"
        bind_port: 8080
    bot_accounts:
      - id: 1
        username: "bot"
        api_key: "API_KEY"
        writable: True
        default: True
    action_custom_config: {}
    """
    with patch("builtins.open", mock_open(read_data=config_content)):
        yield


@pytest.fixture
def mock_os_path_exists():
    with patch("os.path.exists", return_value=True):
        yield


def test_load_config(mock_config_file, mock_os_path_exists):
    from backend.bot_config import load_config
    config = load_config("config.yaml")
    assert config.site_url == "http://example.com"
    assert config.server.bind_address == "127.0.0.1"
    assert config.server.bind_port == 8080
    assert config.redis_host == "localhost"
    assert config.redis_port == 6379
    assert len(config.bot_accounts) == 1
    assert config.bot_accounts[0].id == 1
    assert config.bot_accounts[0].username == "bot"
    assert config.bot_accounts[0].api_key == "API_KEY"
    assert config.bot_accounts[0].writable is True
    assert config.bot_accounts[0].default is True
    assert config.action_custom_config == {}


def test_init_with_existing_config(mock_config_file, mock_os_path_exists):
    from backend.bot_config import config, init, load_config
    with patch("backend.bot_config.load_config", return_value=load_config("config.yaml")):
        init("config.yaml")
        assert config is not None
        assert config.site_url == "http://example.com"


def test_init_without_existing_config():
    with patch("os.path.exists", return_value=False), \
            patch("builtins.open", mock_open()) as mock_init_config_file:
        with pytest.raises(SystemExit):
            from backend.bot_config import config  # noqa: F401
        mock_init_config_file.assert_called_once_with("config.yaml", 'w')
