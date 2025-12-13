import os
import unittest
from unittest.mock import patch, MagicMock
from shared.telemetry import Telemetry

class TestTelemetry(unittest.TestCase):
    def setUp(self):
        # Reset singleton logic if needed or just instantiate directly
        self.telemetry = Telemetry("test_agent", "test_job")

    @patch("shared.telemetry.push_to_gateway")
    def test_record_gauge(self, mock_push):
        # Enable metrics for test
        with patch("shared.telemetry.ENABLE_METRICS", True):
            self.telemetry.register_gauge("test_metric", "doc")
            self.telemetry.record_gauge("test_metric", 42.0)
            
            mock_push.assert_called_once()
            args, kwargs = mock_push.call_args
            self.assertEqual(kwargs['job'], "test_job")
            
            # Verify value in registry
            val = self.telemetry.metrics["test_metric"].collect()[0].samples[0].value
            self.assertEqual(val, 42.0)

    @patch("shared.telemetry.push_to_gateway")
    def test_record_gauge_with_labels(self, mock_push):
        with patch("shared.telemetry.ENABLE_METRICS", True):
            self.telemetry.register_gauge("test_lbl", "doc", ["foo"])
            self.telemetry.record_gauge("test_lbl", 10.0, labels={"foo": "bar"})
            
            # Verify labels in registry
            sample = self.telemetry.metrics["test_lbl"].collect()[0].samples[0]
            self.assertEqual(sample.labels['foo'], 'bar')
            self.assertEqual(sample.value, 10.0)

    def test_log_formatter(self):
        # Verify logger is set up with JSON formatter
        handler = self.telemetry.logger.handlers[0]
        formatter = handler.formatter
        record = logging.LogRecord("test_agent", logging.INFO, "pathname", 1, "test message", {}, None)
        formatted = formatter.format(record)
        import json
        data = json.loads(formatted)
        self.assertEqual(data["message"], "test message")
        self.assertEqual(data["service"], "test_agent")

import logging
if __name__ == "__main__":
    unittest.main()
