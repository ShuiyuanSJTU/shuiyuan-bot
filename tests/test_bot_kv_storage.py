import pytest
from unittest.mock import patch

@pytest.fixture
def mock_db_session():
    with patch('backend.db.DBManager.session', autospec=True) as mock_session:
        yield mock_session

@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config):
    yield

def test_get_existing_key(mock_db_session):
    from backend.bot_kv_storage import KVStorageItem, storage
    mock_session_instance = mock_db_session.return_value.__enter__.return_value
    mock_session_instance.query.return_value.filter_by.return_value.first.return_value = KVStorageItem(key="test_key", value={"data": "test_value"})
    
    result = storage.get("test_key")
    assert result == {"data": "test_value"}

def test_get_non_existing_key(mock_db_session):
    from backend.bot_kv_storage import storage
    mock_session_instance = mock_db_session.return_value.__enter__.return_value
    mock_session_instance.query.return_value.filter_by.return_value.first.return_value = None
    
    result = storage.get("non_existing_key", default="default_value")
    assert result == "default_value"

def test_set_new_key(mock_db_session):
    from backend.bot_kv_storage import storage
    mock_session_instance = mock_db_session.return_value.__enter__.return_value
    mock_session_instance.query.return_value.filter_by.return_value.first.return_value = None
    
    storage.set("new_key", {"data": "new_value"})
    mock_session_instance.add.assert_called_once()
    assert mock_session_instance.add.call_args[0][0].key == "new_key"
    assert mock_session_instance.add.call_args[0][0].value == {"data": "new_value"}

def test_set_existing_key(mock_db_session):
    from backend.bot_kv_storage import KVStorageItem, storage
    mock_session_instance = mock_db_session.return_value.__enter__.return_value
    existing_item = KVStorageItem(key="existing_key", value={"data": "old_value"})
    mock_session_instance.query.return_value.filter_by.return_value.first.return_value = existing_item
    
    storage.set("existing_key", {"data": "new_value"})
    assert existing_item.value == {"data": "new_value"}

def test_delete_existing_key(mock_db_session):
    from backend.bot_kv_storage import KVStorageItem, storage
    mock_session_instance = mock_db_session.return_value.__enter__.return_value
    existing_item = KVStorageItem(key="existing_key", value={"data": "value"})
    mock_session_instance.query.return_value.filter_by.return_value.first.return_value = existing_item
    
    storage.delete("existing_key")
    mock_session_instance.delete.assert_called_once_with(existing_item)

def test_delete_non_existing_key(mock_db_session):
    from backend.bot_kv_storage import storage
    mock_session_instance = mock_db_session.return_value.__enter__.return_value
    mock_session_instance.query.return_value.filter_by.return_value.first.return_value = None
    
    storage.delete("non_existing_key")
    mock_session_instance.delete.assert_not_called()