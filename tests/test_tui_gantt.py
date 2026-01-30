import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import json
from dataclasses import dataclass, field
from typing import List

from shared.tui_gantt import GanttChart
from shared.task_manager import Task

class TestGanttChart(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        # We don't mount the widget, just instantiate
        self.chart = GanttChart(self.project_dir)

    def test_calculate_schedule_no_dependencies(self):
        """Test schedule calculation with no dependencies."""
        self.chart.tasks = [
            Task(id="1", source="sprint", title="Task 1", status="PENDING"),
            Task(id="2", source="sprint", title="Task 2", status="PENDING"),
        ]

        self.chart.calculate_schedule()

        self.assertEqual(self.chart.schedule["1"], 0)
        self.assertEqual(self.chart.schedule["2"], 0)

    def test_calculate_schedule_simple_dependency(self):
        """Test schedule calculation with simple dependency chain: 1 -> 2 -> 3"""
        self.chart.tasks = [
            Task(id="1", source="sprint", title="Task 1", status="PENDING"),
            Task(id="2", source="sprint", title="Task 2", status="PENDING", metadata={"dependencies": ["1"]}),
            Task(id="3", source="sprint", title="Task 3", status="PENDING", metadata={"dependencies": ["2"]}),
        ]

        self.chart.calculate_schedule()

        self.assertEqual(self.chart.schedule["1"], 0)
        self.assertEqual(self.chart.schedule["2"], 1) # 1 + 0
        self.assertEqual(self.chart.schedule["3"], 2) # 1 + 1

    def test_calculate_schedule_branching(self):
        """Test branching dependencies: 1 -> (2, 3) -> 4"""
        self.chart.tasks = [
            Task(id="1", source="sprint", title="Start", status="PENDING"),
            Task(id="2", source="sprint", title="Branch A", status="PENDING", metadata={"dependencies": ["1"]}),
            Task(id="3", source="sprint", title="Branch B", status="PENDING", metadata={"dependencies": ["1"]}),
            Task(id="4", source="sprint", title="End", status="PENDING", metadata={"dependencies": ["2", "3"]}),
        ]

        self.chart.calculate_schedule()

        self.assertEqual(self.chart.schedule["1"], 0)
        self.assertEqual(self.chart.schedule["2"], 1)
        self.assertEqual(self.chart.schedule["3"], 1)
        self.assertEqual(self.chart.schedule["4"], 2) # max(1, 1) + 1

    def test_calculate_schedule_cycle(self):
        """Test cycle handling: 1 -> 2 -> 1. Should not crash."""
        self.chart.tasks = [
            Task(id="1", source="sprint", title="Task 1", status="PENDING", metadata={"dependencies": ["2"]}),
            Task(id="2", source="sprint", title="Task 2", status="PENDING", metadata={"dependencies": ["1"]}),
        ]

        # This will run for max rounds and stop
        self.chart.calculate_schedule()

        # In a cycle 1->2->1 with duration 1:
        # Round 1: 1=0, 2=0
        # Round 2: 1 depends on 2 (start 0) -> 1 start becomes 1. 2 depends on 1 (start 0) -> 2 start becomes 1.
        # Round 3: 1 depends on 2 (start 1) -> 1 start becomes 2. ...
        # It will increment until max_rounds (len(tasks)+1 = 3)
        # So we expect them to be > 0. Exact value depends on order of iteration.

        self.assertGreater(self.chart.schedule["1"], 0)
        self.assertGreater(self.chart.schedule["2"], 0)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_load_schedule(self, mock_read, mock_exists):
        """Test loading tasks from JSON."""
        mock_exists.return_value = True
        mock_data = {
            "tasks": [
                {"id": "A", "title": "Alpha", "status": "COMPLETED", "dependencies": []},
                {"id": "B", "title": "Beta", "status": "PENDING", "dependencies": ["A"]}
            ]
        }
        mock_read.return_value = json.dumps(mock_data)

        # Mock compose/query_one because load_schedule calls it to update status label
        self.chart.query_one = MagicMock()
        self.chart.mount = MagicMock() # Mock mount to avoid widget tree errors

        self.chart.load_schedule()

        self.assertEqual(len(self.chart.tasks), 2)
        self.assertEqual(self.chart.tasks[0].id, "A")
        self.assertEqual(self.chart.schedule["A"], 0)
        self.assertEqual(self.chart.schedule["B"], 1)

if __name__ == '__main__':
    unittest.main()
