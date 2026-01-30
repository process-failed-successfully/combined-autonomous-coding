import unittest
from unittest.mock import patch, MagicMock
from urllib.error import URLError
from shared.telemetry import Telemetry
import time
import logging

class TestTelemetryConnectionError(unittest.TestCase):
    @patch("shared.telemetry.push_to_gateway")
    def test_shutdown_suppresses_connection_error(self, mock_push):
        # Setup: Mock push_to_gateway to raise URLError
        mock_push.side_effect = URLError(ConnectionRefusedError("Connection refused"))

        # Initialize Telemetry
        telemetry = Telemetry("test_service")

        # We need to spy on the logger, not replace it, because the code checks if logger exists
        # But since we initialized it, it exists.
        # The issue with previous test failures "Expected 'warning' to have been called"
        # suggests that telemetry.logger.warning IS called (we see output in stdout),
        # but our mock verification is failing.
        # This is likely because Telemetry.__init__ sets self.logger = logging.getLogger(...)
        # So we need to patch the logger on the instance *after* init.

        mock_logger = MagicMock()
        # Ensure it has the warning attribute so hasattr check passes
        mock_logger.warning = MagicMock()
        telemetry.logger = mock_logger

        # Force a condition where logging happens (bypass throttle)
        telemetry._last_push_error_time = 0

        # Execute: Call _shutdown
        try:
            telemetry._shutdown()
        except Exception as e:
            self.fail(f"_shutdown raised an exception: {e}")

        # Verify
        mock_push.assert_called()
        mock_logger.warning.assert_called()

    @patch("shared.telemetry.push_to_gateway")
    def test_shutdown_suppresses_logging_error(self, mock_push):
        # Setup
        mock_push.side_effect = Exception("Push failed")

        telemetry = Telemetry("test_service_logging_fail")

        mock_logger = MagicMock()
        # Simulate logging failure
        mock_logger.warning.side_effect = ValueError("I/O operation on closed file")
        telemetry.logger = mock_logger

        # Force log
        telemetry._last_push_error_time = 0

        # Execute
        try:
            telemetry._shutdown()
        except Exception as e:
            self.fail(f"_shutdown raised an exception during logging failure: {e}")

        # Verify
        mock_logger.warning.assert_called()

if __name__ == "__main__":
    unittest.main()
