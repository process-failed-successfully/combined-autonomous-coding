import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.redis_lab import RedisLabManager  # noqa: E402


class TestRedisLabManager:
    @pytest.fixture
    def mock_redis(self):
        with patch('shared.redis_lab.redis') as mock_redis_module:
            # If redis is None in source, we need to mock the import or ensure the logic handles it.
            # But the test assumes we want to test the logic when redis IS available.
            # So we patch the module where it's used.
            # shared.redis_lab imports redis inside try/except block.
            # We patch shared.redis_lab.redis attribute directly if it was imported as None,
            # or patch the module if it was imported.

            # Since we want to simulate successful import and usage:
            mock_client = MagicMock()
            mock_redis_module.Redis.from_url.return_value = mock_client

            # Also ensure RedisLabManager sees 'redis' as not None
            with patch('shared.redis_lab.redis', mock_redis_module):
                yield mock_client

    def test_connect_success(self, mock_redis):
        manager = RedisLabManager()
        assert manager.connect() is True
        mock_redis.ping.assert_called_once()

    def test_connect_fail(self):
        # Simulate connection error
        with patch('shared.redis_lab.redis') as mock_redis_module:
            # Ensure ConnectionError is a real exception class for the except block
            mock_redis_module.ConnectionError = Exception
            mock_redis_module.Redis.from_url.side_effect = Exception("Connection failed")

            with patch('shared.redis_lab.redis', mock_redis_module):
                manager = RedisLabManager()
                assert manager.connect() is False

    def test_get_type(self, mock_redis):
        manager = RedisLabManager()
        manager.connect()
        mock_redis.type.return_value = "string"
        assert manager.get_type("mykey") == "string"

    def test_get_ttl(self, mock_redis):
        manager = RedisLabManager()
        manager.connect()
        mock_redis.ttl.return_value = 3600
        assert manager.get_ttl("mykey") == 3600

    def test_get_value_string(self, mock_redis):
        manager = RedisLabManager()
        manager.connect()
        mock_redis.type.return_value = "string"
        mock_redis.get.return_value = "val"
        assert manager.get_value("k") == "val"

    def test_get_value_hash(self, mock_redis):
        manager = RedisLabManager()
        manager.connect()
        mock_redis.type.return_value = "hash"
        mock_redis.hgetall.return_value = {"a": "1"}
        assert manager.get_value("k") == {"a": "1"}

    def test_scan_keys(self, mock_redis):
        manager = RedisLabManager()
        manager.connect()
        # Mock scan: returns (cursor, [keys])
        # First call returns 0 to stop
        mock_redis.scan.return_value = (0, ["k1", "k2"])

        keys = manager.scan_keys("*")
        assert "k1" in keys
        assert "k2" in keys
