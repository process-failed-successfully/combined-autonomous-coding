import unittest
from datetime import datetime, timedelta
import time
from shared.scheduler import Task, parse_duration
from croniter import croniter

class TestSchedulerCron(unittest.TestCase):

    def test_parse_duration(self):
        self.assertEqual(parse_duration("1h"), 3600)
        self.assertEqual(parse_duration("30m"), 1800)
        self.assertEqual(parse_duration("10s"), 10)
        self.assertEqual(parse_duration("1d"), 86400)

    def test_task_interval(self):
        task = Task(name="Test Interval", command="echo hello", interval=60)
        task.last_run = time.time() - 61
        self.assertTrue(task.is_due())

        task.last_run = time.time()
        self.assertFalse(task.is_due())
        self.assertAlmostEqual(task.time_until_due(), 60, delta=1)

    def test_task_cron(self):
        # Expression: every minute
        cron_expr = "* * * * *"
        task = Task(name="Test Cron", command="echo hello", cron_expression=cron_expr)

        # Should initialize last_run to now if not set
        self.assertAlmostEqual(task.last_run, time.time(), delta=1)

        # Not due immediately after init
        self.assertFalse(task.is_due())

        # Calculate next run from now
        now = datetime.now()
        iter = croniter(cron_expr, now)
        next_run = iter.get_next(datetime)
        expected_wait = (next_run - now).total_seconds()

        self.assertAlmostEqual(task.time_until_due(), expected_wait, delta=2)

        # Simulate time passing (move last_run back)
        # If last run was 2 minutes ago, it should be due (passed a minute mark)
        task.last_run = time.time() - 120
        self.assertTrue(task.is_due())

    def test_task_cron_specific(self):
        # specific time (past) - shouldn't be due until next day/hour
        # but is_due checks if next occurrence AFTER last_run is <= now.

        # Let's say scheduled at 5 mins past the hour.
        # Current time: 10:10. Last run: 09:00.
        # Next run after 09:00 was 09:05. 09:05 <= 10:10. True.

        cron_expr = "5 * * * *"
        task = Task(name="Specific Cron", command="echo hello", cron_expression=cron_expr)

        # Mock last_run
        # Use datetime.now().timestamp() instead of time.time() for consistency with timedelta
        last_run_dt = (datetime.now() - timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        task.last_run = last_run_dt.timestamp()

        self.assertTrue(task.is_due())

if __name__ == "__main__":
    unittest.main()
