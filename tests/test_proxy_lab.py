import unittest
from unittest.mock import MagicMock, patch
from shared.proxy_lab import ProxyLabManager, ProxyRequestHandler


class TestProxyLab(unittest.TestCase):
    def test_manager_callback(self):
        """Test that log callback is passed to server."""
        manager = ProxyLabManager(port=0)
        mock_callback = MagicMock()

        # We need to mock serve_forever so start() doesn't block
        with patch('shared.proxy_lab.ThreadedHTTPServer') as MockServer:
            mock_instance = MockServer.return_value
            manager.start(on_log=mock_callback)

            MockServer.assert_called_with(('127.0.0.1', 0), ProxyRequestHandler, log_callback=mock_callback)
            mock_instance.serve_forever.assert_called_once()

    def test_log_methods(self):
        """Test that helper log methods call the callback."""
        # Create a bare object with server attribute
        handler = ProxyRequestHandler.__new__(ProxyRequestHandler)
        handler.server = MagicMock()
        handler.server.log_callback = MagicMock()

        # Test _log_request
        handler._log_request("GET", "http://test.com")
        handler.server.log_callback.assert_called_with("GET http://test.com", "info")

        # Test _log_response
        handler._log_response(200, 0.1, 100)
        handler.server.log_callback.assert_called_with("  -> 200 (0.100s, size: 100)", "response")

        # Test _log_error
        handler._log_error("Test Error")
        handler.server.log_callback.assert_called_with("Test Error", "error")

    def test_start_raises_error(self):
        """Test that start raises OSError if bind fails."""
        manager = ProxyLabManager(port=8080)

        with patch('shared.proxy_lab.ThreadedHTTPServer') as MockServer:
            MockServer.side_effect = OSError("Address in use")
            with self.assertRaises(OSError):
                manager.start(on_log=MagicMock())


if __name__ == '__main__':
    unittest.main()
