import pytest
from unittest.mock import MagicMock

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
    yield mock_config

@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config):
    yield


def test_bot_account_manager_initialization():
    from backend.bot_account_manager import account_manager
    from backend.discourse_api import BotAPI
    assert len(account_manager.bot_clients) == 2
    assert type(account_manager.bot_clients[0]) is BotAPI
    assert type(account_manager.bot_clients[1]) is BotAPI
    assert type(account_manager.default_bot_client) is BotAPI
    assert account_manager.default_bot_client.username == "bot1"
    assert account_manager.usernames == ["bot1", "bot2"]


def test_get_bot_client():
    import backend.bot_account_manager as bot_account_manager
    account_manager = bot_account_manager.account_manager
    bot_client = account_manager.get_bot_client("bot1")
    assert bot_client.username == "bot1"
    with pytest.raises(ValueError):
        account_manager.get_bot_client("nonexistent_bot")


def test_no_bot_account_configured(mock_config):
    mock_config.bot_accounts = []
    with pytest.raises(ValueError, match="No bot account is configured."):
        import backend.bot_account_manager as bot_account_manager  # noqa: F401


def test_multiple_default_bot_accounts_configured(mock_config):
    mock_config.bot_accounts[0].default = True
    mock_config.bot_accounts[1].default = True
    from backend.bot_account_manager import account_manager
    from backend.discourse_api import BotAPI
    assert type(account_manager.default_bot_client) is BotAPI
    assert account_manager.default_bot_client.username == "bot1"


def test_no_default_bot_account_configured(mock_config):
    mock_config.bot_accounts[0].default = False
    mock_config.bot_accounts[1].default = False
    from backend.bot_account_manager import account_manager
    from backend.discourse_api import BotAPI
    assert type(account_manager.default_bot_client) is BotAPI
    assert account_manager.default_bot_client.username == "bot1"