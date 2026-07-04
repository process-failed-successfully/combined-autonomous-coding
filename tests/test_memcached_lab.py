import unittest
from unittest.mock import MagicMock, patch

from shared.memcached_lab import MemcachedLabManager


class TestMemcachedLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MemcachedLabManager(host="localhost", port=11211)

    @patch("shared.memcached_lab.pymemcache")
    @patch("shared.memcached_lab.Client")
    def test_connect_success(self, mock_client_class, mock_pymemcache):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get.return_value = b"test"

        # Act
        result = self.manager.connect()

        # Assert
        self.assertTrue(result)
        mock_client_class.assert_called_once_with(("localhost", 11211))
        mock_client.get.assert_called_once_with('__ping__')

    @patch("shared.memcached_lab.pymemcache")
    @patch("shared.memcached_lab.Client")
    def test_connect_failure(self, mock_client_class, mock_pymemcache):
        # Arrange
        mock_client_class.side_effect = Exception("Connection refused")

        # Act
        result = self.manager.connect()

        # Assert
        self.assertFalse(result)

    @patch("shared.memcached_lab.pymemcache")
    @patch("shared.memcached_lab.Client")
    def test_get_success(self, mock_client_class, mock_pymemcache):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get.return_value = b"my_value"

        # Act
        result = self.manager.get("my_key")

        # Assert
        self.assertEqual(result, "my_value")
        mock_client.get.assert_any_call("my_key")

    @patch("shared.memcached_lab.pymemcache")
    @patch("shared.memcached_lab.Client")
    def test_get_not_found(self, mock_client_class, mock_pymemcache):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get.return_value = None

        # Act
        result = self.manager.get("missing_key")

        # Assert
        self.assertIsNone(result)

    @patch("shared.memcached_lab.pymemcache")
    @patch("shared.memcached_lab.Client")
    def test_set_success(self, mock_client_class, mock_pymemcache):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.set.return_value = True

        # Act
        result = self.manager.set("my_key", "my_value", ex=60)

        # Assert
        self.assertTrue(result)
        mock_client.set.assert_called_once_with("my_key", b"my_value", expire=60)

    @patch("shared.memcached_lab.pymemcache")
    @patch("shared.memcached_lab.Client")
    def test_delete_success(self, mock_client_class, mock_pymemcache):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.delete.return_value = True

        # Act
        result = self.manager.delete("my_key")

        # Assert
        self.assertTrue(result)
        mock_client.delete.assert_called_once_with("my_key")

    @patch("shared.memcached_lab.pymemcache")
    @patch("shared.memcached_lab.Client")
    def test_flush_success(self, mock_client_class, mock_pymemcache):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Act
        result = self.manager.flush()

        # Assert
        self.assertTrue(result)
        mock_client.flush_all.assert_called_once()

    @patch("shared.memcached_lab.pymemcache")
    @patch("shared.memcached_lab.Client")
    def test_stats_success(self, mock_client_class, mock_pymemcache):
        # Arrange
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.stats.return_value = {b"uptime": b"12345", b"version": b"1.6.9"}

        # Act
        result = self.manager.stats()

        # Assert
        self.assertEqual(result, {"uptime": "12345", "version": "1.6.9"})
        mock_client.stats.assert_called_once()

if __name__ == "__main__":
    unittest.main()
