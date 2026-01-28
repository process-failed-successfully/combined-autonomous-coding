import unittest
import time
from datetime import datetime
from shared.scheduler import Task, parse_duration

class TestSchedulerCron(unittest.TestCase):
    def test_parse_duration(self):
        self.assertEqual(parse_duration("1h"), 3600)
        self.assertEqual(parse_duration("30m"), 1800)
        self.assertEqual(parse_duration("10s"), 10)
        self.assertEqual(parse_duration("1d"), 86400)

    def test_task_interval(self):
        task = Task(name="test", command="echo", interval=60)
        task.last_run = time.time() - 61
        self.assertTrue(task.is_due())

        task.last_run = time.time()
        self.assertFalse(task.is_due())

    def test_task_cron(self):
        # Expression: every minute
        task = Task(name="cron_test", command="echo", cron_expression="* * * * *")

        # If never run, it should be due (returns 0.0)
        task.last_run = 0.0
        self.assertTrue(task.is_due())

        # Determine current time
        now_ts = time.time()
        now_dt = datetime.fromtimestamp(now_ts)

        # Set last run to exactly now (assume we just ran)
        task.last_run = now_ts

        # Next run should be at start of next minute
        next_ts = task.get_next_run_time()
        next_dt = datetime.fromtimestamp(next_ts)

        self.assertGreater(next_ts, now_ts)
        # Should be within 60 seconds
        self.assertLess(next_ts, now_ts + 61)

        # Check if due
        self.assertFalse(task.is_due())

        # Simulate time passing (move forward 65 seconds)
        # We can't change time.time(), so we check logic manually
        # If time.time() was next_ts + 1, is_due() should be True

        # Mock time.time in logic if we want, or just verify get_next_run_time logic
        self.assertEqual(next_dt.second, 0)

if __name__ == '__main__':
    unittest.main()
