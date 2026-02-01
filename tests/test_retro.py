
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from shared.retro import RetrospectiveConductor
from shared.log_explorer import AgentStep

class TestRetrospectiveConductor(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.conductor = RetrospectiveConductor(self.project_dir)

    def test_detect_patterns(self):
        steps = [
            AgentStep(1, "10:00:00", "Action 1", "Details", "ACTION"),
            AgentStep(2, "10:00:01", "Action 1", "Details", "ACTION"),
            AgentStep(3, "10:00:02", "Action 1", "Details", "ACTION"),
            AgentStep(4, "10:00:03", "Action 1", "Details", "ACTION"), # 4th time -> loop
            AgentStep(5, "10:00:04", "Error A", "Details", "ERROR"),
            AgentStep(6, "10:00:05", "Error A", "Details", "ERROR"), # 2nd time -> repeated error
        ]

        patterns = self.conductor.detect_patterns(steps)

        loop_pattern = next((p for p in patterns if p["type"] == "potential_loop"), None)
        error_pattern = next((p for p in patterns if p["type"] == "repeated_error"), None)

        self.assertIsNotNone(loop_pattern)
        self.assertEqual(loop_pattern["description"], "Action 1")
        self.assertEqual(loop_pattern["count"], 4)

        self.assertIsNotNone(error_pattern)
        self.assertEqual(error_pattern["description"], "Error A")
        self.assertEqual(error_pattern["count"], 2)

    @patch("shared.retro.LogParser")
    @patch("shared.retro.CostCalculator")
    def test_analyze_run(self, MockCostCalculator, MockLogParser):
        # Mock dependencies
        mock_parser = MockLogParser.return_value
        mock_parser.parse_run.return_value = [
            AgentStep(1, "10:00:00", "Start", "", "INFO"),
            AgentStep(2, "10:00:10", "Action", "", "ACTION"),
            AgentStep(3, "10:00:20", "Error", "", "ERROR"),
            AgentStep(4, "10:00:30", "End", "", "INFO"),
        ]

        mock_cost = MockCostCalculator.return_value
        mock_cost.calculate_run_cost.return_value = {"total_cost": 0.50}

        # Inject mocks into conductor
        self.conductor.log_parser = mock_parser
        self.conductor.cost_calculator = mock_cost

        # Mock get_run_log_path to return a dummy path
        with patch.object(self.conductor, 'get_run_log_path', return_value=Path("dummy.log")) as mock_path:
            # Mock Path.stat().st_mtime
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value.st_mtime = 1600000000

                metrics = self.conductor.analyze_run("run_123")

                self.assertEqual(metrics["run_id"], "run_123")
                self.assertEqual(metrics["total_steps"], 4)
                self.assertEqual(metrics["errors"], 1)
                self.assertEqual(metrics["actions"], 1)
                self.assertEqual(metrics["cost"], 0.50)
                # Duration: 30s
                self.assertEqual(metrics["duration_seconds"], 30.0)

    @patch("shared.retro.GeminiAgent")
    async def test_generate_report(self, MockAgent):
        # Mock Agent
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=("COMPLETED", "Mock Report Content", []))

        analysis = {
            "run_id": "test_run",
            "duration_seconds": 60,
            "cost": 0.1,
            "total_steps": 10,
            "errors": 0,
            "actions": 5,
            "patterns": [],
            "steps": []
        }

        report = await self.conductor.generate_report(analysis)

        self.assertEqual(report, "Mock Report Content")
        mock_agent_instance.run_agent_session.assert_called_once()

if __name__ == "__main__":
    unittest.main()
