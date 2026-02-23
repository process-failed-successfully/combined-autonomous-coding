import unittest
import shutil
import time
import json
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.productivity_lab import ProductivityManager, run_productivity_lab_logic

class TestProductivityLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_prod_lab_data")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()
        self.manager = ProductivityManager(self.test_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_start_saves_active_session(self):
        self.manager.start_session("work", "task-1")

        # Verify active in memory
        self.assertIsNotNone(self.manager.current_session)
        self.assertEqual(self.manager.current_session.type, "work")

        # Verify persistence by creating a new manager
        new_manager = ProductivityManager(self.test_dir)
        self.assertIsNotNone(new_manager.current_session)
        self.assertEqual(new_manager.current_session.task_id, "task-1")

    def test_stop_clears_active_and_saves_history(self):
        self.manager.start_session("break")
        time.sleep(0.1) # Ensure some duration
        self.manager.stop_session()

        # Verify memory
        self.assertIsNone(self.manager.current_session)
        self.assertEqual(len(self.manager.sessions), 1)
        self.assertGreater(self.manager.sessions[0].duration, 0)

        # Verify persistence
        new_manager = ProductivityManager(self.test_dir)
        self.assertIsNone(new_manager.current_session)
        self.assertEqual(len(new_manager.sessions), 1)

    def test_log_distraction(self):
        self.manager.log_distraction("Slack notification")

        new_manager = ProductivityManager(self.test_dir)
        self.assertEqual(len(new_manager.distractions), 1)
        self.assertEqual(new_manager.distractions[0].description, "Slack notification")

    def test_stats_calculation(self):
        self.manager.start_session("work")
        time.sleep(0.1)
        self.manager.stop_session()

        self.manager.start_session("break")
        time.sleep(0.1)
        self.manager.stop_session()

        stats = self.manager.get_today_stats()
        self.assertGreater(stats["work_time"], 0)
        self.assertGreater(stats["break_time"], 0)
        self.assertEqual(stats["sessions_count"], 2)

    @patch('sys.exit')
    @patch('builtins.print')
    def test_cli_logic_start(self, mock_print, mock_exit):
        args = argparse.Namespace(
            project_dir=self.test_dir,
            action="start",
            type="work",
            task="CLI Task"
        )

        run_productivity_lab_logic(args)

        # Check persistence
        new_manager = ProductivityManager(self.test_dir)
        self.assertIsNotNone(new_manager.current_session)
        self.assertEqual(new_manager.current_session.task_id, "CLI Task")

    @patch('sys.exit')
    @patch('builtins.print')
    def test_cli_logic_stop(self, mock_print, mock_exit):
        # Start first
        self.manager.start_session("work")

        args = argparse.Namespace(
            project_dir=self.test_dir,
            action="stop"
        )

        run_productivity_lab_logic(args)

        # Check persistence
        new_manager = ProductivityManager(self.test_dir)
        self.assertIsNone(new_manager.current_session)
        self.assertEqual(len(new_manager.sessions), 1)

if __name__ == '__main__':
    unittest.main()
