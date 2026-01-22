import sys
from typing import Any
from pathlib import Path
import unittest
from unittest.mock import patch

# Ensure shared can be imported
sys.path.append(str(Path(__file__).parent.parent))

from shared.analytics import collect_analytics_data  # noqa: E402


class TestTUIAnalyticsLogic(unittest.TestCase):
    def setUp(self) -> None:
        self.project_dir = Path("/tmp/test_project")

    @patch("shared.debt.scan_todos")
    @patch("shared.debt.analyze_project_complexity")
    @patch("shared.debt.find_duplicates")
    @patch("shared.debt.UnusedCodeDetector")
    @patch("shared.security.SecurityAuditor.scan_secrets")
    def test_collect_analytics_data(self, mock_scan_secrets: Any, MockUnused: Any, mock_duplication: Any, mock_complexity: Any, mock_todos: Any) -> None:
        # Mock Data for Debt
        mock_todos.return_value = [{"tag": "TODO", "text": "Fix"}]
        mock_complexity.return_value = [{"function": "f", "complexity": 5}]
        mock_duplication.return_value = []
        MockUnused.return_value.get_unused_definitions.return_value = []

        # Mock Data for Security
        mock_scan_secrets.return_value = [
            {"severity": "HIGH", "type": "secret", "file": "foo.py", "line": 1, "description": "AWS Key"}
        ]

        # Call the actual function
        data = collect_analytics_data(self.project_dir)

        # Assertions on structure
        self.assertIn("debt", data)
        self.assertIn("security", data)

        # Debt assertions
        self.assertEqual(data["debt"]["metrics"]["todos"]["count"], 1)
        # 1 todo = 1 point -> A
        self.assertEqual(data["debt"]["grade"], "A")

        # Security assertions
        self.assertEqual(len(data["security"]), 1)
        self.assertEqual(data["security"][0]["severity"], "HIGH")


if __name__ == "__main__":
    unittest.main()
