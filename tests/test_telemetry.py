import logging
import unittest
from unittest.mock import patch
from shared.telemetry import Telemetry


class TestTelemetry(unittest.TestCase):
    def setUp(self):
        # Reset singleton logic if needed or just instantiate directly
        self.telemetry = Telemetry("test_agent", "test_job")
        self.telemetry.synchronous_mode = True

    @patch("shared.telemetry.push_to_gateway")
    def test_record_gauge_with_autofilled_labels(self, mock_push):
        # Enable metrics for test
        with patch("shared.telemetry.ENABLE_METRICS", True):
            self.telemetry._last_push_time = 0.0

            self.telemetry.register_gauge("test_metric", "doc", ["agent_id"])
            self.telemetry.record_gauge("test_metric", 42.0)

            mock_push.assert_called_once()
            args, kwargs = mock_push.call_args
            self.assertEqual(kwargs["job"], "test_job")

            # Verify value in registry
            val = self.telemetry.metrics["test_metric"].collect()[0].samples[0].value
            self.assertEqual(val, 42.0)
            label_keys = self.telemetry.metrics["test_metric"].collect()[0].samples[0].labels.keys()
            self.assertIn("agent_id", label_keys)

    @patch("shared.telemetry.push_to_gateway")
    def test_record_gauge_no_labels(self, mock_push):
        """Verify that gauges with no labels are handled correctly."""
        with patch("shared.telemetry.ENABLE_METRICS", True):
            self.telemetry._last_push_time = 0.0

            self.telemetry.register_gauge("test_no_labels_metric", "doc", [])
            self.telemetry.record_gauge("test_no_labels_metric", 123.0)

            mock_push.assert_called_once()
            args, kwargs = mock_push.call_args
            self.assertEqual(kwargs["job"], "test_job")

            # Verify value in registry - no .labels() call needed
            val = self.telemetry.metrics["test_no_labels_metric"].collect()[0].samples[0].value
            self.assertEqual(val, 123.0)
            labels = self.telemetry.metrics["test_no_labels_metric"].collect()[0].samples[0].labels
            self.assertEqual(labels, {})

    @patch("shared.telemetry.push_to_gateway")
    def test_record_gauge_with_labels(self, mock_push):
        with patch("shared.telemetry.ENABLE_METRICS", True):
            self.telemetry.register_gauge("test_lbl", "doc", ["foo"])
            self.telemetry.record_gauge("test_lbl", 10.0, labels={"foo": "bar"})

            # Verify labels in registry
            sample = self.telemetry.metrics["test_lbl"].collect()[0].samples[0]
            self.assertEqual(sample.labels["foo"], "bar")
            self.assertEqual(sample.value, 10.0)

    def test_log_formatter(self):
        # Verify logger is set up with JSON formatter
        handler = self.telemetry.logger.handlers[0]
        formatter = handler.formatter
        record = logging.LogRecord(
            "test_agent", logging.INFO, "pathname", 1, "test message", {}, None
        )
        formatted = formatter.format(record)
        import json

        data = json.loads(formatted)
        self.assertEqual(data["message"], "test message")
        self.assertEqual(data["service"], "test_agent")

    @patch("shared.telemetry.push_to_gateway")
    def test_increment_counter_no_labels(self, mock_push):
        """Verify that counters with no labels are handled correctly."""
        with patch("shared.telemetry.ENABLE_METRICS", True):
            self.telemetry._last_push_time = 0.0

            self.telemetry.register_counter("test_counter_no_labels", "doc", [])
            self.telemetry.increment_counter("test_counter_no_labels", 5.0)

            mock_push.assert_called_once()
            args, kwargs = mock_push.call_args
            self.assertEqual(kwargs["job"], "test_job")

            val = self.telemetry.metrics["test_counter_no_labels"].collect()[0].samples[0].value
            self.assertEqual(val, 5.0)
            labels = self.telemetry.metrics["test_counter_no_labels"].collect()[0].samples[0].labels
            self.assertEqual(labels, {})

    @patch("shared.telemetry.push_to_gateway")
    def test_record_histogram_no_labels(self, mock_push):
        """Verify that histograms with no labels are handled correctly."""
        with patch("shared.telemetry.ENABLE_METRICS", True):
            self.telemetry._last_push_time = 0.0

            self.telemetry.register_histogram("test_histogram_no_labels", "doc", [])
            self.telemetry.record_histogram("test_histogram_no_labels", 1.23)

            mock_push.assert_called_once()
            args, kwargs = mock_push.call_args
            self.assertEqual(kwargs["job"], "test_job")

            val = self.telemetry.metrics["test_histogram_no_labels"]._sum._value
            self.assertEqual(val, 1.23)
            for sample in self.telemetry.metrics["test_histogram_no_labels"].collect()[0].samples:
                # Histograms will have 'le' label for buckets, but no others
                if sample.name.endswith('_bucket'):
                    self.assertEqual(list(sample.labels.keys()), ['le'])


if __name__ == "__main__":
    unittest.main()
