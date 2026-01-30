import unittest
from unittest.mock import MagicMock, patch
import time
from shared.telemetry import Telemetry

class TestTelemetryConnectionError(unittest.TestCase):
    def setUp(self):
        # Reset singleton if necessary, or just create a new instance with a unique name
        self.telemetry = Telemetry("test_service", project_name="test_project")
        # Ensure we can log
        self.telemetry._last_push_error_time = 0

    @patch("shared.telemetry.push_to_gateway")
    def test_push_metrics_sync_suppresses_logging_error(self, mock_push):
        # Simulate connection error
        mock_push.side_effect = Exception("Connection refused")

        # Mock logger to simulate closed file
        self.telemetry.logger = MagicMock()
        self.telemetry.logger.warning.side_effect = ValueError("I/O operation on closed file")

        # Call _push_metrics_sync
        try:
            self.telemetry._push_metrics_sync()
        except ValueError:
            self.fail("_push_metrics_sync raised ValueError unexpectedly")
        except Exception as e:
            self.fail(f"_push_metrics_sync raised unexpected exception: {e}")

        # Verify push_to_gateway was called
        mock_push.assert_called()

        # Verify logger.warning was called (and triggered the side effect)
        self.telemetry.logger.warning.assert_called()

if __name__ == "__main__":
    unittest.main()
