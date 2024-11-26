import pytest
from unittest.mock import patch, MagicMock, create_autospec


@pytest.fixture
def mock_config():
    mock_config = MagicMock()
    mock_config.redis_host = "localhost"
    mock_config.redis_port = 6379
    return mock_config


@pytest.fixture
def patch_bot_account_manager():
    mock_bot_account_manager = create_autospec('backend.bot_account_manager')
    mock_bot_account_manager.account_manager = MagicMock()
    with patch.dict('sys.modules', {'backend.bot_account_manager': mock_bot_account_manager}):
        yield


@pytest.fixture
def mock_redis_client():
    with patch("redis.Redis") as mock_redis:
        yield mock_redis


@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config, patch_bot_account_manager, mock_redis_client):
    yield


def test_redis_client_initialization(mock_config, mock_redis_client):
    import backend.utils.redis_cache as redis_cache
    client = redis_cache.RedisClient(
        host=mock_config.redis_host, port=mock_config.redis_port).client
    assert client is not None
    mock_redis_client.assert_called_once_with(
        host="localhost", port=6379, db=0)


def test_redis_cache_decorator():
    import backend.utils.redis_cache as redis_cache
    client = redis_cache.RedisClient().client

    @redis_cache.redis_cache(cache_key="test_key", ex=60)
    def test_function(x):
        return x * 2

    client.get = MagicMock(return_value=None)
    client.set = MagicMock()

    result = test_function(5)
    assert result == 10

    client.set.assert_called_once_with("test_key", '10', ex=60)

    client.get = MagicMock(return_value=b'20')
    result = test_function(5)
    assert result == 20


def test_redis_cache_decorator_with_callable_key():
    import backend.utils.redis_cache as redis_cache
    client = redis_cache.RedisClient().client

    @redis_cache.redis_cache(cache_key=lambda x: f"key_{x}", ex=60)
    def test_function(x):
        return x * 2

    client.get = MagicMock(return_value=None)
    client.set = MagicMock()

    result = test_function(5)
    assert result == 10

    client.set.assert_called_once_with("key_5", '10', ex=60)

    client.get = MagicMock(return_value=b'20')
    result = test_function(5)
    assert result == 20


def test_redis_cache_decorator_when_redis_unavailable():
    with patch("redis.Redis", side_effect=Exception("Connection Error")) as mock_redis:
        import backend.utils.redis_cache as redis_cache

        assert redis_cache._redis_available is False
        assert redis_cache._redis_client is None

        @redis_cache.redis_cache(cache_key="test_key", ex=60)
        def test_function(x):
            return x * 2

        result = test_function(5)
        assert result == 10

        assert redis_cache._redis_available is False
        assert redis_cache._redis_client is None
