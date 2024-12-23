import pytest
from unittest.mock import MagicMock, create_autospec, patch
from backend.discourse_api import BotAPI
import sys


@pytest.fixture(autouse=True)
def unload_backend_after_each_test():
    yield
    for module in list(sys.modules.keys()):
        if module.startswith('backend.') or module == 'backend':
            del sys.modules[module]


@pytest.fixture
def mock_bot_api():
    with patch('backend.discourse_api.BotAPI', autospec=True) as mock_api:
        instance = mock_api.return_value
        for method_name in dir(BotAPI):
            if callable(getattr(BotAPI, method_name)) and not method_name.startswith("__"):
                setattr(instance, method_name, MagicMock())
        yield instance


@pytest.fixture
def bypass_db_init():
    mock_db = create_autospec('backend.db')
    mock_db.DBManager = MagicMock()
    mock_db.db_manager = mock_db.DBManager
    with patch.dict('sys.modules', {'backend.db': mock_db}):
        yield mock_config


@pytest.fixture
def patch_bot_config(mock_config):
    mock_bot_config = create_autospec('backend.bot_config')
    mock_bot_config.config = mock_config
    with patch.dict('sys.modules', {'backend.bot_config': mock_bot_config}):
        yield mock_config


@pytest.fixture
def mock_config_base():
    mock_config = MagicMock()
    mock_config.site_url = "http://example.com"
    mock_config.bot_accounts = [
        MagicMock(id=1, username="bot1", api_key="API",
                  writable=True, default=True),
    ]
    mock_config.action_custom_config = {}
    mock_config.limited_mode = False
    mock_config.db_url = "sqlite:///:memory:"
    yield mock_config


@pytest.fixture
def mock_config(mock_config_base):
    yield mock_config_base


@pytest.fixture
def patch_bot_kv_storage(mock_kv_storage):
    mock_bot_kv_storage = create_autospec('backend.bot_kv_storage')
    mock_bot_kv_storage.storage = MagicMock()
    mock_bot_kv_storage.storage.get.side_effect = mock_kv_storage.get
    mock_bot_kv_storage.storage.set.side_effect = mock_kv_storage.__setitem__
    mock_bot_kv_storage.storage.delete.side_effect = mock_kv_storage.__delitem__
    with patch.dict('sys.modules', {'backend.bot_kv_storage': mock_bot_kv_storage}):
        yield mock_kv_storage

@pytest.fixture
def mock_kv_storage(mock_kv_storage_base):
    yield mock_kv_storage_base

@pytest.fixture
def mock_kv_storage_base():
    return {"kv_storage": {}}