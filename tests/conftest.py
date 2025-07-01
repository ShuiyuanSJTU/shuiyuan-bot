import pytest
from unittest.mock import MagicMock, create_autospec, patch
import os
import sys
import random
import string

@pytest.fixture(scope="session", autouse=True)
def rename_config_file():
    if os.path.exists('config.yaml'):
        bak_random = ''.join(random.choices(string.ascii_lowercase, k=8))
        os.rename('config.yaml', f'config.yaml.{bak_random}.bak')
        yield
        os.rename(f'config.yaml.{bak_random}.bak', 'config.yaml')
    else:
        yield

@pytest.fixture(autouse=True)
def unload_backend_after_each_test():
    yield
    for module in list(sys.modules.keys()):
        if module.startswith('backend.') or module == 'backend':
            del sys.modules[module]

@pytest.fixture(autouse=True)
def mock_bot_api():
    with patch('backend.discourse_api.Discourse', autospec=True) as mock_api:
        mock_api.return_value = MagicMock()
        yield mock_api.return_value

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