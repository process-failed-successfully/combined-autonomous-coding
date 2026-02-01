import unittest
import json
from pathlib import Path
import tempfile
import shutil
from io import StringIO
from unittest.mock import patch

from shared.cli_gantt import GanttCLI, run_gantt_logic

class TestGanttCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.sprint_plan_path = self.test_dir / "sprint_plan.json"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_sprint_plan(self, tasks):
        data = {
            "sprint_goal": "Test Goal",
            "tasks": tasks
        }
        self.sprint_plan_path.write_text(json.dumps(data))

    def test_load_tasks_success(self):
        tasks = [
            {"id": "1", "title": "Task 1", "status": "PENDING", "dependencies": []},
            {"id": "2", "title": "Task 2", "status": "IN_PROGRESS", "dependencies": ["1"]}
        ]
        self.create_sprint_plan(tasks)

        cli = GanttCLI(self.test_dir)
        self.assertTrue(cli.load_tasks())
        self.assertEqual(len(cli.tasks), 2)
        self.assertEqual(cli.tasks[0].id, "1")
        self.assertEqual(cli.tasks[1].id, "2")
        self.assertEqual(cli.tasks[1].metadata["dependencies"], ["1"])

    def test_load_tasks_no_file(self):
        cli = GanttCLI(self.test_dir)
        # Capture stdout to silence error message during test
        with patch('sys.stdout', new=StringIO()):
            self.assertFalse(cli.load_tasks())

    def test_calculate_schedule_independent(self):
        tasks = [
            {"id": "1", "title": "Task 1", "dependencies": []},
            {"id": "2", "title": "Task 2", "dependencies": []}
        ]
        self.create_sprint_plan(tasks)
        cli = GanttCLI(self.test_dir)
        cli.load_tasks()
        cli.calculate_schedule()

        self.assertEqual(cli.schedule["1"], 0)
        self.assertEqual(cli.schedule["2"], 0)

    def test_calculate_schedule_chain(self):
        tasks = [
            {"id": "1", "title": "Task 1", "dependencies": []},
            {"id": "2", "title": "Task 2", "dependencies": ["1"]},
            {"id": "3", "title": "Task 3", "dependencies": ["2"]}
        ]
        self.create_sprint_plan(tasks)
        cli = GanttCLI(self.test_dir)
        cli.load_tasks()
        cli.calculate_schedule()

        self.assertEqual(cli.schedule["1"], 0)
        self.assertEqual(cli.schedule["2"], 1) # 0 + 1
        self.assertEqual(cli.schedule["3"], 2) # 1 + 1

    def test_render(self):
        tasks = [
            {"id": "1", "title": "Task 1", "status": "COMPLETED", "dependencies": []},
            {"id": "2", "title": "Task 2", "status": "PENDING", "dependencies": ["1"]}
        ]
        self.create_sprint_plan(tasks)
        cli = GanttCLI(self.test_dir)
        cli.load_tasks()
        cli.calculate_schedule()

        with patch('sys.stdout', new=StringIO()) as fake_out:
            cli.render()
            output = fake_out.getvalue()

        self.assertIn("Task 1", output)
        self.assertIn("Task 2", output)
        # Check for bar characters (simplified check)
        self.assertIn("████", output)

    def test_run_gantt_logic_integration(self):
        tasks = [{"id": "1", "title": "Task 1", "dependencies": []}]
        self.create_sprint_plan(tasks)

        with patch('sys.stdout', new=StringIO()):
            success = run_gantt_logic(self.test_dir)
            self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()
