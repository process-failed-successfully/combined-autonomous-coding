import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.metrics_lab import MetricsLabManager, SystemCollector

class TestMetricsLab(unittest.TestCase):
    def setUp(self):
        self.manager = MetricsLabManager()
        # Suppress console output during tests
        self.manager.console = MagicMock()

    @patch('shared.metrics_lab.requests.get')
    def test_scrape_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = """
# HELP http_requests_total The total number of HTTP requests.
# TYPE http_requests_total counter
http_requests_total{method="post",code="200"} 1027 1395066363000
http_requests_total{method="post",code="400"}    3 1395066363000
"""
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        self.manager.scrape("http://localhost:8080/metrics")

        # Verify console output calls
        # We expect a table to be printed.
        self.manager.console.print.assert_called()
        # Verify call args contain expected strings?
        # Rich objects are hard to inspect directly, but we can assume success if no exception.

    @patch('shared.metrics_lab.requests.get')
    def test_lint_warnings(self, mock_get):
        mock_response = MagicMock()
        # Missing HELP/TYPE and bad naming
        mock_response.text = """
my_metric 10
# TYPE bad_counter counter
bad_counter 5
"""
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with self.assertRaises(SystemExit) as cm:
            self.manager.lint("http://localhost:8080/metrics")
        self.assertEqual(cm.exception.code, 1)

        # Should print warnings
        calls = self.manager.console.print.call_args_list
        messages = [str(call[0][0]) for call in calls]

        found_warning_help = any("Missing HELP" in m for m in messages)
        found_warning_type = any("Missing TYPE" in m for m in messages)
        found_error_naming = any("MUST end with '_total'" in m for m in messages)

        self.assertTrue(found_warning_help, "Should warn about missing HELP")
        self.assertTrue(found_warning_type, "Should warn about missing TYPE")
        self.assertTrue(found_error_naming, "Should error about naming")

    @patch('shared.monitor_lab.MonitorLabManager')
    def test_system_collector(self, MockMonitor):
        mock_monitor = MockMonitor.return_value
        mock_monitor.get_system_stats.return_value = {
            "cpu": 50.0,
            "memory": {"used": 1000, "free": 2000, "total": 3000},
            "disk": {"used": 500, "free": 500, "total": 1000}
        }

        collector = SystemCollector()
        metrics = list(collector.collect())

        self.assertEqual(len(metrics), 3) # CPU, Memory, Disk

        cpu = next(m for m in metrics if m.name == 'system_cpu_usage_percent')
        self.assertEqual(cpu.samples[0].value, 50.0)

        mem = next(m for m in metrics if m.name == 'system_memory_usage_bytes')
        # Check samples for mem
        total = next(s for s in mem.samples if s.labels['type'] == 'total')
        self.assertEqual(total.value, 3000)

    @patch('shared.metrics_lab.make_server')
    @patch('shared.metrics_lab.make_wsgi_app')
    @patch('shared.metrics_lab.REGISTRY')
    def test_serve(self, mock_registry, mock_make_app, mock_make_server):
        mock_server = MagicMock()
        mock_make_server.return_value = mock_server

        # Mock KeyboardInterrupt to stop server immediately
        mock_server.serve_forever.side_effect = KeyboardInterrupt

        self.manager.serve(9000)

        mock_registry.register.assert_called()
        mock_make_server.assert_called_with('', 9000, mock_make_app.return_value)
        mock_server.serve_forever.assert_called()

if __name__ == '__main__':
    unittest.main()
