import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import yaml
import sys
from shared.scheduler import Scheduler, parse_duration, Task

class TestScheduler(unittest.TestCase):
    def test_parse_duration(self):
        self.assertEqual(parse_duration("10s"), 10)
        self.assertEqual(parse_duration("5m"), 300)
        self.assertEqual(parse_duration("1h"), 3600)
        self.assertEqual(parse_duration("1d"), 86400)
        self.assertEqual(parse_duration("30"), 30)
        with self.assertRaises(ValueError):
            parse_duration("invalid")

    def test_task_due(self):
        task = Task("test", "echo", 60)
        task.last_run = 0
        self.assertTrue(task.is_due())

        import time
        task.last_run = time.time()
        self.assertFalse(task.is_due())

        task.last_run = time.time() - 61
        self.assertTrue(task.is_due())

    def test_init_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            scheduler = Scheduler(project_dir)
            self.assertTrue(scheduler.init_config())
            self.assertTrue(scheduler.config_path.exists())

            # Check content
            with open(scheduler.config_path) as f:
                data = yaml.safe_load(f)
            self.assertIn("tasks", data)
            self.assertEqual(len(data["tasks"]), 2)

            # Should return False if exists
            self.assertFalse(scheduler.init_config())

    def test_load_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            scheduler = Scheduler(project_dir)

            config_data = {
                "tasks": [
                    {"name": "t1", "command": "cmd1", "interval": "10s"},
                    {"name": "t2", "command": "cmd2", "interval": "1m"}
                ]
            }
            with open(scheduler.config_path, "w") as f:
                yaml.dump(config_data, f)

            scheduler.load_config()
            self.assertEqual(len(scheduler.tasks), 2)
            self.assertEqual(scheduler.tasks[0].name, "t1")
            self.assertEqual(scheduler.tasks[0].interval, 10)
            self.assertEqual(scheduler.tasks[1].interval, 60)

    @patch("subprocess.run")
    def test_run_task(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="done", stderr="")

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            scheduler = Scheduler(project_dir)
            task = Task("test", "echo hello", 10)

            scheduler.run_task(task)

            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            self.assertEqual(kwargs["cwd"], project_dir)
            # Check last_run updated
            self.assertGreater(task.last_run, 0)

if __name__ == "__main__":
    unittest.main()
