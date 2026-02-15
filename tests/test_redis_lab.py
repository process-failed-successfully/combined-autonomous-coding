import unittest
from unittest.mock import MagicMock, patch
import sys
import io
import types
import argparse

# We need to mock 'redis' before importing shared.redis_lab if it's not installed
# or if we want to force usage of the mock.
# However, if shared.redis_lab is already imported, we might need to reload it or patch it.

# Let's ensure a mock redis exists in sys.modules
if 'redis' not in sys.modules:
    mock_redis_module = types.ModuleType('redis')
    # Mock ConnectionError class
    class MockConnectionError(Exception): pass
    mock_redis_module.ConnectionError = MockConnectionError
    # Mock Redis class
    mock_redis_module.Redis = MagicMock()
    sys.modules['redis'] = mock_redis_module

# Now we can import
from shared import redis_lab
# If redis was missing, redis_lab.redis is None. We need to patch it.
if redis_lab.redis is None:
    redis_lab.redis = sys.modules['redis']

from shared.redis_lab import RedisLabManager, run_redis_lab_logic

class TestRedisLab(unittest.TestCase):
    def setUp(self):
        self.mock_redis_patcher = patch('redis.Redis.from_url')
        self.mock_from_url = self.mock_redis_patcher.start()
        self.mock_client = MagicMock()
        self.mock_from_url.return_value = self.mock_client

        self.manager = RedisLabManager()

    def tearDown(self):
        self.mock_redis_patcher.stop()

    def test_connect(self):
        self.assertTrue(self.manager.connect())
        self.mock_from_url.assert_called_with("redis://localhost:6379/0", decode_responses=True)
        self.mock_client.ping.assert_called_once()

    def test_get(self):
        self.mock_client.get.return_value = "value"
        self.assertEqual(self.manager.get("key"), "value")
        self.mock_client.get.assert_called_with("key")

    def test_set(self):
        self.mock_client.set.return_value = True
        self.assertTrue(self.manager.set("key", "value", ex=60))
        self.mock_client.set.assert_called_with("key", "value", ex=60)

    def test_delete(self):
        self.mock_client.delete.return_value = 1
        self.assertEqual(self.manager.delete("key"), 1)
        self.mock_client.delete.assert_called_with("key")

    def test_keys(self):
        self.mock_client.keys.return_value = ["k1", "k2"]
        self.assertEqual(self.manager.keys("*"), ["k1", "k2"])
        self.mock_client.keys.assert_called_with("*")

    def test_flush(self):
        self.mock_client.flushdb.return_value = True
        self.assertTrue(self.manager.flush())
        self.mock_client.flushdb.assert_called_once()

    def test_info(self):
        self.mock_client.info.return_value = {"redis_version": "7.0"}
        self.assertEqual(self.manager.info(), {"redis_version": "7.0"})
        self.mock_client.info.assert_called_once()

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_get(self, mock_stderr, mock_stdout):
        args = argparse.Namespace(action="get", key="mykey", url=None)
        self.mock_client.get.return_value = "myvalue"

        with self.assertRaises(SystemExit) as cm:
            run_redis_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("myvalue", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_connect_success(self, mock_stdout):
        args = argparse.Namespace(action="connect", url=None)
        with self.assertRaises(SystemExit) as cm:
            run_redis_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Connected", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
