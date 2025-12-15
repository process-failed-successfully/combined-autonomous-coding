from shared.telemetry import init_telemetry
import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestIterationMetrics(unittest.TestCase):
    def setUp(self):
        # Reset telemetry
        self.telemetry = init_telemetry(
            "test_service", agent_type="test", project_name="test_project"
        )

    def test_iteration_metrics_registered(self):
        """Verify that iteration metrics are registered during initialization."""
        expected_metrics = [
            "agent_iteration",
            "agent_iterations_total",
            "iteration_duration_seconds",
        ]

        for metric in expected_metrics:
            self.assertIn(
                metric, self.telemetry.metrics, f"Metric {metric} not registered"
            )

        # Check help string for the new metric
        self.assertEqual(
            self.telemetry.metrics["iteration_duration_seconds"]._documentation,
            "Time taken for the last iteration",
        )


if __name__ == "__main__":
    # Strip known args that might be passed by the runner
    clean_argv = [sys.argv[0]]
    for arg in sys.argv[1:]:
        if not arg.startswith("--dashboard-url") and not arg.startswith(
            "--no-dashboard"
        ):
            clean_argv.append(arg)
    sys.argv = clean_argv

    unittest.main()
