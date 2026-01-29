
import unittest
import logging
from unittest.mock import MagicMock, patch
import socket
from urllib.error import URLError
from shared.telemetry import Telemetry

class TestTelemetryConnectionError(unittest.TestCase):
    @patch('shared.telemetry.push_to_gateway')
    def test_shutdown_with_connection_error(self, mock_push):
        # Setup: Simulate connection error
        mock_push.side_effect = URLError(socket.error(111, 'Connection refused'))

        # Initialize telemetry
        t = Telemetry("test_service")

        # Simulate Logger closed (which happens during atexit/shutdown sometimes)
        # We can simulate this by making the logger raise an error on log
        t.logger = MagicMock()
        t.logger.warning.side_effect = ValueError("I/O operation on closed file")

        # Execution: Trigger _shutdown (which calls _push_metrics(sync=True))
        try:
            t._shutdown()
        except Exception as e:
            self.fail(f"_shutdown raised exception: {e}")

        # Verify: Warning was attempted (even if it failed internally and was caught)
        t.logger.warning.assert_called()

if __name__ == '__main__':
    unittest.main()
