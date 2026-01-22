import sys
import shutil
import tempfile
from typing import Any
from pathlib import Path
import unittest
from unittest.mock import patch

# Ensure shared can be imported
sys.path.append(str(Path(__file__).parent.parent))

from shared.analytics import (  # noqa: E402
    collect_analytics_data,
    get_git_contributors,
    get_git_hotspots,
    get_git_activity
)


class TestTUIAnalyticsLogic(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

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

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_get_git_contributors(self, mock_which: Any, mock_run: Any) -> None:
        mock_which.return_value = "/usr/bin/git"
        mock_run.return_value.stdout = "10\tAlice\n5\tBob"
        mock_run.return_value.returncode = 0

        contributors = get_git_contributors(self.project_dir)
        self.assertEqual(len(contributors), 2)
        self.assertEqual(contributors[0], (10, "Alice"))
        self.assertEqual(contributors[1], (5, "Bob"))

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_get_git_hotspots(self, mock_which: Any, mock_run: Any) -> None:
        mock_which.return_value = "/usr/bin/git"
        mock_run.return_value.stdout = "file1.py\nfile1.py\nfile2.py"
        mock_run.return_value.returncode = 0

        hotspots = get_git_hotspots(self.project_dir, limit=5)
        self.assertEqual(len(hotspots), 2)
        self.assertEqual(hotspots[0], ("file1.py", 2))
        self.assertEqual(hotspots[1], ("file2.py", 1))

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_get_git_activity(self, mock_which: Any, mock_run: Any) -> None:
        mock_which.return_value = "/usr/bin/git"
        mock_run.return_value.stdout = "2023-01-01\n2023-01-01\n2023-01-02"
        mock_run.return_value.returncode = 0

        activity = get_git_activity(self.project_dir)
        self.assertEqual(len(activity), 2)
        self.assertEqual(activity[0], ("2023-01-01", 2))
        self.assertEqual(activity[1], ("2023-01-02", 1))


if __name__ == "__main__":
    unittest.main()
