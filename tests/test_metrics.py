import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.telemetry import Telemetry, init_telemetry, get_telemetry


class TestTelemetry(unittest.TestCase):
    def setUp(self):
        # Reset singleton and metrics for each test
        Telemetry._instance = None
        self.telemetry = init_telemetry(
            "test_service", agent_type="test", project_name="test_project"
        )
        # Mock push_to_gateway to prevent actual network calls
        self.patcher = patch("shared.telemetry.push_to_gateway")
        self.mock_push = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_singleton(self):
        t1 = get_telemetry()
        t2 = get_telemetry()
        self.assertIs(t1, t2)
        self.assertEqual(t1.service_name, "test_service")

    def test_counter_increment(self):
        self.telemetry.register_counter("test_counter", "Test doc", ["label1"])
        self.telemetry.increment_counter("test_counter", 1, {"label1": "A"})

        # Check if push was called
        self.mock_push.assert_called()

        # Check value (internal registry access)
        val = self.telemetry.metrics["test_counter"].labels(label1="A")._value.get()
        self.assertEqual(val, 1.0)

    def test_label_injection(self):
        self.telemetry.register_counter(
            "test_auto_label", "Test doc", ["agent_id", "project", "custom"]
        )
        self.telemetry.increment_counter("test_auto_label", 1, {"custom": "C"})

        # Verify agent_id and project were injected
        # We need to access the metric sample
        # Note: 'agent_id' matches self.service_name in the implementation logic
        metric = self.telemetry.metrics["test_auto_label"]
        # Access the sample with injected labels
        val = metric.labels(agent_id="test_service", project="test_project", custom="C")
        self.assertEqual(val._value.get(), 1.0)

    def test_histogram(self):
        self.telemetry.register_histogram("test_hist", "Test hist", ["label1"])
        self.telemetry.record_histogram("test_hist", 0.5, {"label1": "H"})

        # Verify observation
        metric = self.telemetry.metrics["test_hist"]
        self.assertEqual(metric.labels(label1="H")._sum.get(), 0.5)


if __name__ == "__main__":
    unittest.main()
