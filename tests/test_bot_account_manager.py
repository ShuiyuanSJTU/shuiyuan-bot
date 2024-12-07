import pytest
import sys
import importlib
from unittest.mock import patch, MagicMock, create_autospec

@pytest.fixture
def mock_config():
    mock_config = MagicMock()
    mock_config.site_url = "http://example.com"
    mock_config.bot_accounts = [
        MagicMock(id=1, username="bot1", api_key="API_KEY_1",
                  writable=True, default=True),
        MagicMock(id=2, username="bot2", api_key="API_KEY_2",
                  writable=True, default=False)
    ]
    return mock_config


@pytest.fixture
def mock_bot_api():
    with patch("backend.bot_account_manager.BotAPI") as mock_bot_api:
        yield mock_bot_api


@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config, mock_bot_api):
    yield


def test_bot_account_manager_initialization():
    import backend.bot_account_manager as bot_account_manager
    account_manager = bot_account_manager.account_manager
    assert len(account_manager.bot_clients) == 2
    assert account_manager.default_bot_client.username == "bot1"
    assert account_manager.usernames == ["bot1", "bot2"]


def test_get_bot_client():
    import backend.bot_account_manager as bot_account_manager
    account_manager = bot_account_manager.account_manager
    bot_client = account_manager.get_bot_client("bot1")
    assert bot_client.username == "bot1"
    with pytest.raises(ValueError):
        account_manager.get_bot_client("nonexistent_bot")


def test_no_bot_account_configured():
    mock_config = MagicMock()
    mock_bot_config = create_autospec('backend.bot_config')
    mock_bot_config.config = mock_config
    mock_config.bot_accounts = []
    with patch.dict('sys.modules', {'backend.bot_config': mock_bot_config}):
        import backend.bot_account_manager as bot_account_manager
        with pytest.raises(ValueError, match="No bot account is configured."):
            importlib.reload(bot_account_manager)
