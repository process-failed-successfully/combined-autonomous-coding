import unittest
import json
import shutil
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure shared modules can be imported
sys.path.append(str(Path(__file__).parent.parent))

from shared.day_planner import DayPlannerManager, TimeBlock

class TestDayPlannerManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("/tmp/test_day_planner")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.manager = DayPlannerManager(self.test_dir)

        # Mock TaskManager
        self.manager.task_manager = MagicMock()
        self.mock_task = MagicMock()
        self.mock_task.id = "task-1"
        self.mock_task.title = "Important Task"
        self.mock_task.priority = "High"
        self.manager.task_manager.fetch_all_tasks.return_value = [self.mock_task]

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_add_block_success(self):
        today = date.today()
        block_id = self.manager.add_block(today, "09:00", 60, "Meeting")
        self.assertIsNotNone(block_id)

        plan = self.manager.get_plan(today)
        self.assertEqual(len(plan.blocks), 1)
        self.assertEqual(plan.blocks[0].title, "Meeting")
        self.assertEqual(plan.blocks[0].start_time, "09:00")

    def test_add_block_conflict(self):
        today = date.today()
        # 09:00 - 10:00
        self.manager.add_block(today, "09:00", 60, "Meeting 1")

        # 09:30 - 10:30 (Overlap)
        result = self.manager.add_block(today, "09:30", 60, "Meeting 2")
        self.assertIsNone(result)

        plan = self.manager.get_plan(today)
        self.assertEqual(len(plan.blocks), 1)

    def test_remove_block(self):
        today = date.today()
        block_id = self.manager.add_block(today, "10:00", 30, "Break")
        self.assertTrue(self.manager.remove_block(today, block_id))

        plan = self.manager.get_plan(today)
        self.assertEqual(len(plan.blocks), 0)

    def test_update_notes(self):
        today = date.today()
        self.manager.update_notes(today, "Focus on deep work.")
        plan = self.manager.get_plan(today)
        self.assertEqual(plan.notes, "Focus on deep work.")

    def test_persistence(self):
        today = date.today()
        self.manager.add_block(today, "11:00", 60, "Coding")

        # New manager instance
        new_manager = DayPlannerManager(self.test_dir)
        plan = new_manager.get_plan(today)
        self.assertEqual(len(plan.blocks), 1)
        self.assertEqual(plan.blocks[0].title, "Coding")

    def test_auto_schedule(self):
        today = date.today()
        # Mock fetch_all_tasks is already set up in setUp

        count = self.manager.auto_schedule(today)
        self.assertEqual(count, 1)

        plan = self.manager.get_plan(today)
        self.assertEqual(len(plan.blocks), 1)
        self.assertEqual(plan.blocks[0].task_id, "task-1")
        self.assertEqual(plan.blocks[0].start_time, "09:00")

    def test_get_unscheduled_tasks(self):
        today = date.today()
        # Initially unscheduled
        tasks = self.manager.get_unscheduled_tasks(today)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, "task-1")

        # Schedule it
        self.manager.add_block(today, "14:00", 30, "Work", task_id="task-1")

        tasks_after = self.manager.get_unscheduled_tasks(today)
        self.assertEqual(len(tasks_after), 0)

if __name__ == '__main__':
    unittest.main()
