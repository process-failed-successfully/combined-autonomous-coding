from shared.debt import DebtCollector
import unittest
from unittest.mock import patch
from pathlib import Path
import sys

# Ensure shared can be imported
sys.path.append(str(Path(__file__).parent.parent))


class TestDebtCollector(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.collector = DebtCollector(self.project_dir)

    @patch("shared.debt.scan_todos")
    @patch("shared.debt.analyze_project_complexity")
    @patch("shared.debt.find_duplicates")
    @patch("shared.debt.UnusedCodeDetector")
    def test_collect_metrics(self, MockUnused, mock_duplication, mock_complexity, mock_todos):
        # Setup mocks
        mock_todos.return_value = [
            {"tag": "TODO", "text": "Fix this"},
            {"tag": "FIXME", "text": "Broken"}
        ]

        mock_complexity.return_value = [
            {"function": "func1", "complexity": 5},
            {"function": "func2", "complexity": 15},  # High complexity (excess 5)
            {"function": "func3", "complexity": 20}  # High complexity (excess 10)
        ]

        mock_duplication.return_value = [
            {"token_count": 100, "locations": []},
            {"token_count": 50, "locations": []}
        ]

        mock_unused_instance = MockUnused.return_value
        mock_unused_instance.get_unused_definitions.return_value = [
            {"name": "unused_func", "type": "function"},
            {"name": "UnusedClass", "type": "class"}
        ]

        # Run collection
        metrics = self.collector.collect()

        # Verify calls
        mock_todos.assert_called_once()
        mock_complexity.assert_called_once()
        mock_duplication.assert_called_once()
        mock_unused_instance.scan.assert_called_once()

        # Verify results
        self.assertEqual(metrics["todos"]["count"], 2)

        self.assertEqual(metrics["complexity"]["high_risk_count"], 2)  # func2, func3
        # func2 (15): excess 5
        # func3 (20): excess 10
        # total excess: 15
        self.assertEqual(metrics["complexity"]["total_excess"], 15)

        self.assertEqual(metrics["duplication"]["blocks"], 2)
        self.assertEqual(metrics["duplication"]["total_tokens"], 150)

        self.assertEqual(metrics["unused"]["count"], 2)

    def test_calculate_score_exact(self):
        """Verifies the score calculation based on the defined formula."""
        metrics = {
            "todos": {"count": 10},
            # 10 * 1 = 10 pts

            "complexity": {"high_risk_count": 5, "total_excess": 20},
            # 5 * 5 = 25 pts (high risk count)
            # 20 * 1 = 20 pts (total excess)
            # Total Complexity = 45 pts

            "duplication": {"total_tokens": 200},
            # 200 / 10 = 20 pts

            "unused": {"count": 4}
            # 4 * 5 = 20 pts
        }

        expected_score = 10 + 45 + 20 + 20  # = 95

        score, grade = self.collector.calculate_score(metrics)

        self.assertEqual(score, 95.0)
        # 95 is "B" (51-150)
        self.assertEqual(grade, "B")

    def test_calculate_score_grade_boundaries(self):
        # Test A (< 50)
        metrics_a = {
            "todos": {"count": 0},
            "complexity": {"high_risk_count": 0, "total_excess": 0},
            "duplication": {"total_tokens": 0},
            "unused": {"count": 0}
        }
        score, grade = self.collector.calculate_score(metrics_a)
        self.assertEqual(score, 0)
        self.assertEqual(grade, "A")

        # Test F (> 500)
        metrics_f = {
            "todos": {"count": 600},  # 600 pts
            "complexity": {"high_risk_count": 0, "total_excess": 0},
            "duplication": {"total_tokens": 0},
            "unused": {"count": 0}
        }
        score, grade = self.collector.calculate_score(metrics_f)
        self.assertEqual(score, 600)
        self.assertEqual(grade, "F")


if __name__ == "__main__":
    unittest.main()
