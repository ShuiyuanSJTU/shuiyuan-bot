import pytest
from unittest.mock import patch, MagicMock, create_autospec
import importlib


@pytest.fixture
def mock_config():
    mock_config.site_url = "http://example.com"
    mock_config.bot_accounts = [
        MagicMock(id=1, username="bot1", api_key="API_KEY_1",
                  writable=True, default=True),
        MagicMock(id=2, username="bot2", api_key="API_KEY_2",
                  writable=True, default=False)
    ]
    mock_config.action_custom_config = {}
    return mock_config


@pytest.fixture
def mock_pkgutil():
    with patch("backend.plugins.pkgutil.iter_modules") as mock_iter_modules:
        yield mock_iter_modules


@pytest.fixture
def mock_importlib():
    with patch("backend.plugins.importlib.import_module") as mock_import_module:
        yield mock_import_module


@pytest.fixture
def mock_register_bot_action():
    with patch("backend.plugins.register_bot_action") as mock_register:
        yield mock_register


def test_load_plugins(patch_bot_config, mock_pkgutil, mock_importlib, mock_register_bot_action):
    from backend.plugins import load_plugins
    from backend.bot_action import BotAction
    # Mock the return value of iter_modules
    mock_pkgutil.return_value = [
        (None, 'module1', True),
        (None, 'module2', True),
        (None, '_private_module', True)
    ]

    # Mock the imported modules
    mock_module1 = MagicMock()
    mock_module1.__all__ = ['BotAction1']
    mock_module1.BotAction1 = type('BotAction1', (BotAction,), {
                                   'action_name': 'Action1'})

    mock_module2 = MagicMock()
    mock_module2.__all__ = ['BotAction2']
    mock_module2.BotAction2 = type('BotAction2', (BotAction,), {
                                   'action_name': 'Action2'})

    mock_importlib.side_effect = lambda name: {
        'backend.plugins.module1': mock_module1,
        'backend.plugins.module2': mock_module2
    }[name]

    # Call the function to test
    load_plugins()

    # Assertions
    mock_pkgutil.assert_called_once()
    mock_importlib.assert_any_call('backend.plugins.module1')
    mock_importlib.assert_any_call('backend.plugins.module2')
    mock_register_bot_action.assert_any_call(mock_module1.BotAction1)
    mock_register_bot_action.assert_any_call(mock_module2.BotAction2)
