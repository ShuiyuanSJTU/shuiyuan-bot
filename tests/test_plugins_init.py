import pytest
from unittest.mock import patch, MagicMock
import importlib


@pytest.fixture
def mock_config(mock_config_base):
    mock_config_base.bot_accounts = [
        MagicMock(id=1, username="bot1", api_key="API_KEY_1",
                  writable=True, default=True),
        MagicMock(id=2, username="bot2", api_key="API_KEY_2",
                  writable=True, default=False)
    ]
    mock_config_base.action_custom_config = {}
    return mock_config_base


@pytest.fixture
def mock_pkgutil():
    with patch("backend.plugins.pkgutil.iter_modules") as mock_iter_modules:
        yield mock_iter_modules


@pytest.fixture
def mock_importlib():
    with patch("backend.plugins.importlib.import_module") as mock_import_module:
        yield mock_import_module


def test_load_plugins(patch_bot_config, bypass_db_init, mock_pkgutil, mock_importlib):
    from backend.plugins import load_plugins
    from backend.bot_action import BotAction
    from backend.bot_manager import bot_manager as BotManager
    from backend.db import db_manager as DBManager
    DBManager.init_tables = MagicMock()
    BotManager.register_bot_action = MagicMock()
    # Mock the return value of iter_modules
    mock_pkgutil.return_value = [
        (None, 'module1', True),
        (None, 'module2', True),
        (None, 'module3', True),
        (None, 'module4', True),
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

    mock_module3 = MagicMock()
    mock_module3.BotAction3 = type('BotAction3', (BotAction,), {
                                   'action_name': 'Action3'})
    
    mock_module4 = MagicMock()
    mock_module4.__all__ = ['BotAction4']
    mock_module4.BotAction4 = type('BotAction4', (BotAction,), {})

    mock_importlib.side_effect = lambda name: {
        'backend.plugins.module1': mock_module1,
        'backend.plugins.module2': mock_module2,
        'backend.plugins.module3': mock_module3,
        'backend.plugins.module4': mock_module4,
    }[name]

    # Call the function to test
    load_plugins()

    # Assertions
    mock_pkgutil.assert_called_once()
    mock_importlib.assert_any_call('backend.plugins.module1')
    mock_importlib.assert_any_call('backend.plugins.module2')
    mock_importlib.assert_any_call('backend.plugins.module3')
    mock_importlib.assert_any_call('backend.plugins.module4')
    assert 'backend.plugins._private_module' not in mock_importlib.call_args_list
    BotManager.register_bot_action.assert_any_call(mock_module1.BotAction1)
    BotManager.register_bot_action.assert_any_call(mock_module2.BotAction2)
    BotManager.register_bot_action.assert_any_call(mock_module3.BotAction3)
    assert mock_module4.BotAction4 not in BotManager.register_bot_action.call_args_list
    DBManager.init_tables.assert_called_once()
