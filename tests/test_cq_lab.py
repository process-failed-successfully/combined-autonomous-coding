import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import json
import tempfile
import shutil
import sys

from shared.cq_lab import CodeQualityManager

# Only import TUI if we are in an environment that might support it,
# but for unit testing widgets we usually don't need a full display.
try:
    from textual.app import App
    from shared.tui_cq import CodeQualityTab
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False

class TestCodeQualityManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = CodeQualityManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shared.cq_lab.analyze_project_complexity")
    @patch("shared.cq_lab.find_duplicates")
    @patch("shared.cq_lab.SecurityAuditor")
    @patch("shared.cq_lab.DebtCollector")
    @patch("shared.cq_lab.CodeStatsManager")
    def test_collect_metrics(self, mock_stats, mock_debt, mock_sec, mock_dup, mock_comp):
        # Mock complexity
        mock_comp.return_value = [
            {"complexity": 5, "function": "func1", "file": "a.py", "lineno": 1},
            {"complexity": 15, "function": "complex_func", "file": "b.py", "lineno": 10},
        ]

        # Mock duplication
        mock_dup.return_value = [
            {"token_count": 100, "locations": []}
        ]

        # Mock Security
        mock_auditor = mock_sec.return_value
        mock_auditor.run_all.return_value = [
            {"severity": "HIGH", "description": "Bad thing", "type": "secret", "file": "s.py", "line": 1}
        ]

        # Mock Debt
        mock_debt_instance = mock_debt.return_value
        mock_debt_instance.collect.return_value = {
            "todos": {"count": 5, "items": []},
            "unused": {"count": 2, "items": []}
        }

        # Mock Stats
        mock_stats_instance = mock_stats.return_value
        mock_stats_instance.scan.return_value = {
            "Python": {"files": 10, "lines": 1000, "code": 800, "comment": 100, "blank": 100}
        }

        metrics = self.manager.collect_metrics()

        # Assertions
        self.assertEqual(metrics["complexity"]["max"], 15)
        self.assertEqual(metrics["complexity"]["high_risk_count"], 1)
        self.assertEqual(metrics["complexity"]["average"], 10.0)

        self.assertEqual(metrics["duplication"]["blocks"], 1)
        self.assertEqual(metrics["duplication"]["total_tokens"], 100)

        self.assertEqual(metrics["security"]["high"], 1)
        self.assertEqual(metrics["security"]["count"], 1)

        self.assertEqual(metrics["debt"]["todos"], 5)
        self.assertEqual(metrics["debt"]["unused"], 2)

    def test_calculate_score(self):
        # Create a synthetic metrics dict
        metrics = {
            "complexity": {"high_risk_count": 0, "average": 5.0},
            "duplication": {"blocks": 0, "total_tokens": 0},
            "security": {"high": 0, "medium": 0, "low": 0},
            "debt": {"todos": 0, "unused": 0}
        }

        # Perfect score
        res = self.manager.calculate_score(metrics)
        self.assertEqual(res["score"], 100)
        self.assertEqual(res["grade"], "A")

        # High Penalty
        metrics["security"]["high"] = 5 # 5 * 20 = 100 penalty
        res = self.manager.calculate_score(metrics)
        self.assertEqual(res["score"], 0)
        self.assertEqual(res["grade"], "F")

        # Mixed
        metrics["security"]["high"] = 0
        metrics["complexity"]["high_risk_count"] = 5 # 10 pts
        metrics["debt"]["todos"] = 20 # 10 pts
        # Total penalty = 20
        res = self.manager.calculate_score(metrics)
        self.assertEqual(res["score"], 80)
        self.assertEqual(res["grade"], "B")

    def test_history(self):
        score_data = {
            "score": 85,
            "grade": "B",
            "penalties": {}
        }
        self.manager.save_history(score_data)

        history = self.manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["score"], 85)
        self.assertEqual(history[0]["grade"], "B")

        # Test appending
        score_data_2 = {
            "score": 95,
            "grade": "A",
            "penalties": {}
        }
        self.manager.save_history(score_data_2)
        history = self.manager.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["score"], 95)

class TestCQTab(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(HAS_TEXTUAL, "Textual not installed")
    async def test_tui_compose(self):
        # Minimal app to hold the widget
        class TestApp(App):
            def compose(self):
                yield CodeQualityTab(Path("."))

        app = TestApp()
        async with app.run_test() as pilot:
            # Check if widgets exist
            assert pilot.app.query_one("CodeQualityTab") is not None
            assert pilot.app.query_one("#cq-grade-lbl") is not None
            assert pilot.app.query_one("#btn-cq-refresh") is not None

if __name__ == '__main__':
    unittest.main()
