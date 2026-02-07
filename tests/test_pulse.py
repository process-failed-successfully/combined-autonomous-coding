
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime, timedelta

# Import the class to be tested (not yet created, but we mock dependencies)
# We will import PulseManager from shared.pulse once created.
# For now, we assume the structure.

class TestPulse(unittest.TestCase):

    def setUp(self):
        # We need to import inside the test method or setup if the module doesn't exist yet
        # But for TDD, we usually write the test first.
        # However, since we can't import a non-existent module, we will create the test file
        # assuming the module will be available when we run the tests.
        pass

    @patch("shared.pulse.PulseManager.collect_metrics")
    def test_calculate_health_score_perfect(self, mock_collect):
        from shared.pulse import PulseManager
        manager = PulseManager(Path("."))

        today = datetime.now().strftime("%Y-%m-%d")

        # Perfect scenario
        metrics = {
            "complexity": [],
            "todos": [],
            "security": [],
            "activity": [(today, 5)] # Some activity
        }

        score = manager.calculate_health_score(metrics)
        self.assertEqual(score, 100)

    @patch("shared.pulse.PulseManager.collect_metrics")
    def test_calculate_health_score_complexity(self, mock_collect):
        from shared.pulse import PulseManager
        manager = PulseManager(Path("."))

        today = datetime.now().strftime("%Y-%m-%d")

        # High complexity files
        # 3 files with complexity > 10. Penalty: 3 * 5 = 15. Score: 85.
        metrics = {
            "complexity": [
                {"file": "a.py", "complexity": 12},
                {"file": "b.py", "complexity": 15},
                {"file": "c.py", "complexity": 11},
                {"file": "d.py", "complexity": 5},
            ],
            "todos": [],
            "security": [],
            "activity": [(today, 5)]
        }

        score = manager.calculate_health_score(metrics)
        self.assertEqual(score, 85)

    @patch("shared.pulse.PulseManager.collect_metrics")
    def test_calculate_health_score_todos(self, mock_collect):
        from shared.pulse import PulseManager
        manager = PulseManager(Path("."))

        today = datetime.now().strftime("%Y-%m-%d")

        # Many TODOs
        # 12 TODOs. Penalty: floor(12/5) * 1 = 2. Score: 98.
        metrics = {
            "complexity": [],
            "todos": [{"tag": "TODO"}] * 12,
            "security": [],
            "activity": [(today, 5)]
        }

        score = manager.calculate_health_score(metrics)
        self.assertEqual(score, 98)

    @patch("shared.pulse.PulseManager.collect_metrics")
    def test_calculate_health_score_security(self, mock_collect):
        from shared.pulse import PulseManager
        manager = PulseManager(Path("."))

        today = datetime.now().strftime("%Y-%m-%d")

        # Security issues
        # 1 HIGH (-10), 2 MEDIUM (-5 * 2 = -10). Total -20. Score: 80.
        metrics = {
            "complexity": [],
            "todos": [],
            "security": [
                {"severity": "HIGH"},
                {"severity": "MEDIUM"},
                {"severity": "medium"}, # case insensitive check
            ],
            "activity": [(today, 5)]
        }

        score = manager.calculate_health_score(metrics)
        self.assertEqual(score, 80)

    @patch("shared.pulse.PulseManager.collect_metrics")
    def test_calculate_health_score_inactive(self, mock_collect):
        from shared.pulse import PulseManager
        manager = PulseManager(Path("."))

        # Inactive
        # No activity in last 7 days. Penalty: -10. Score: 90.
        metrics = {
            "complexity": [],
            "todos": [],
            "security": [],
            "activity": [] # Empty activity
        }

        score = manager.calculate_health_score(metrics)
        self.assertEqual(score, 90)

    @patch("shared.pulse.PulseManager.collect_metrics")
    def test_calculate_health_score_capped(self, mock_collect):
        from shared.pulse import PulseManager
        manager = PulseManager(Path("."))

        # Everything bad
        metrics = {
            "complexity": [{"complexity": 20}] * 10, # -50 (capped at -30)
            "todos": [{"tag": "TODO"}] * 200, # -40 (capped at -20)
            "security": [{"severity": "HIGH"}] * 10, # -100 (capped at -40)
            "activity": [] # -10
        }
        # Total penalty: 30 + 20 + 40 + 10 = 100. Score: 0.

        score = manager.calculate_health_score(metrics)
        self.assertEqual(score, 0)

if __name__ == '__main__':
    unittest.main()
