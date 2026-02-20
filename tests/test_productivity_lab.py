import unittest
import shutil
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.productivity_lab import ProductivityManager, ProductivitySession

class TestProductivityManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = ProductivityManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_start_stop_session(self):
        with patch('time.time', return_value=1000.0):
            self.manager.start_session("work", "task-1")

        self.assertIsNotNone(self.manager.current_session)
        self.assertEqual(self.manager.current_session.type, "work")
        self.assertEqual(self.manager.current_session.start_time, 1000.0)
        self.assertEqual(self.manager.current_session.task_id, "task-1")

        with patch('time.time', return_value=1500.0):
            self.manager.stop_session()

        self.assertIsNone(self.manager.current_session)
        self.assertEqual(len(self.manager.sessions), 1)
        session = self.manager.sessions[0]
        self.assertEqual(session.duration, 500.0)
        self.assertEqual(session.end_time, 1500.0)

    def test_persistence(self):
        with patch('time.time', return_value=1000.0):
            self.manager.start_session("work")
        with patch('time.time', return_value=1100.0):
            self.manager.stop_session()

        # Reload
        new_manager = ProductivityManager(self.test_dir)
        self.assertEqual(len(new_manager.sessions), 1)
        self.assertEqual(new_manager.sessions[0].duration, 100.0)

    def test_get_today_stats(self):
        # Create session today
        now = time.time()
        with patch('time.time', return_value=now):
            self.manager.start_session("work")
        with patch('time.time', return_value=now + 60):
            self.manager.stop_session()

        stats = self.manager.get_today_stats()
        self.assertEqual(stats["work_time"], 60.0)
        self.assertEqual(stats["sessions_count"], 1)

    def test_log_distraction(self):
        self.manager.log_distraction("phone")
        self.assertEqual(len(self.manager.distractions), 1)
        self.assertEqual(self.manager.distractions[0].description, "phone")
