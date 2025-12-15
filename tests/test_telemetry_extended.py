import unittest
from unittest.mock import patch, MagicMock, ANY
import logging
import time
from shared.telemetry import Telemetry, get_telemetry, init_telemetry


class TestTelemetryExtended(unittest.TestCase):
    def setUp(self):
        # Reset singleton logic if needed or just instantiate directly
        self.telemetry = Telemetry("test_agent", "test_job")

    @patch("shared.telemetry.push_to_gateway")
    def test_record_histogram(self, mock_push):
        with patch("shared.telemetry.ENABLE_METRICS", True):
            self.telemetry.register_histogram("test_hist", "doc", ["agent_id"])
            self.telemetry.record_histogram("test_hist", 5.0)

            mock_push.assert_called_once()

            # Verify bucket counts or sum
            metric = self.telemetry.metrics["test_hist"]
            self.assertIsNotNone(metric)

    @patch("shared.telemetry.push_to_gateway")
    def test_increment_counter(self, mock_push):
        with patch("shared.telemetry.ENABLE_METRICS", True):
            self.telemetry.register_counter("test_counter", "doc", ["agent_id"])
            self.telemetry.increment_counter("test_counter")

            mock_push.assert_called_once()

            val = self.telemetry.metrics["test_counter"].collect()[0].samples[0].value
            self.assertEqual(val, 1.0)

    @patch("shared.telemetry.push_to_gateway")
    def test_disabled_metrics(self, mock_push):
        with patch("shared.telemetry.ENABLE_METRICS", False):
            self.telemetry.register_gauge("test_gauge", "doc", ["agent_id"])
            self.telemetry.record_gauge("test_gauge", 100.0)
            mock_push.assert_not_called()

    @patch("shared.telemetry.push_to_gateway")
    def test_log_error(self, mock_push):
        with patch("shared.telemetry.ENABLE_METRICS", True):
            # This should increment agent_errors_total
            self.telemetry.log_error("Somethign went wrong")

            # agent_errors_total is registered in init
            val = (
                self.telemetry.metrics["agent_errors_total"]
                .collect()[0]
                .samples[0]
                .value
            )
            self.assertEqual(val, 1.0)

    def test_capture_logs_from(self):
        other_logger = logging.getLogger("other_logger")
        self.telemetry.capture_logs_from("other_logger")
        self.assertIn(self.telemetry.file_handler, other_logger.handlers)

    def test_init_telemetry(self):
        t = init_telemetry("svc", "type", "proj")
        self.assertEqual(t.service_name, "svc")
        self.assertEqual(get_telemetry(), t)

    def test_get_telemetry_fallback(self):
        # Reset global
        import shared.telemetry

        shared.telemetry._telemetry = None

        t = get_telemetry()
        self.assertEqual(t.service_name, "default_agent")

    @patch("shared.telemetry.push_to_gateway")
    def test_push_metrics_exception(self, mock_push):
        mock_push.side_effect = Exception("Push failed")
        # Should not raise exception
        self.telemetry._push_metrics()

    @patch("psutil.Process")
    def test_system_monitoring_loop(self, mock_process):
        mock_p = MagicMock()
        mock_p.memory_info.return_value.rss = 1000
        mock_p.cpu_percent.return_value = 10.0
        mock_p.children.return_value = []
        mock_process.return_value = mock_p

        with (
            patch("shared.telemetry.ENABLE_METRICS", True),
            patch("shared.telemetry.push_to_gateway") as mock_push,
        ):

            self.telemetry.monitoring_active = True

            # We want to run one loop iteration then stop
            # We can override time.sleep to stop the loop or just run the logic manually?
            # _system_monitoring_loop is a loop while self.monitoring_active
            # We can start it in a thread and stop it quickly.

            def side_effect_sleep(sec):
                self.telemetry.monitoring_active = False

            with patch("time.sleep", side_effect=side_effect_sleep):
                self.telemetry._system_monitoring_loop()

            # Check if metrics were recorded
            # container_memory_usage_bytes
            val = (
                self.telemetry.metrics["container_memory_usage_bytes"]
                .collect()[0]
                .samples[0]
                .value
            )
            self.assertEqual(val, 1000)


if __name__ == "__main__":
    unittest.main()
