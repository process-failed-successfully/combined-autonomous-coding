import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.badges import BadgeManager, Badge

class TestBadgeManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        # We mock resolve because /tmp/test_project might not exist
        with patch("pathlib.Path.resolve", return_value=self.project_dir):
            self.manager = BadgeManager(self.project_dir)

    @patch("shared.badges.shutil.which")
    @patch("shared.badges.run_command")
    @patch("shared.badges.scan_todos")
    def test_generate_badges_all_success(self, mock_scan, mock_run, mock_which):
        # Setup mocks
        mock_which.return_value = "/usr/bin/tool"

        # Test output: "TOTAL ... 85%"
        mock_run.side_effect = [
            # pytest
            MagicMock(returncode=0, stdout="TOTAL 100 85 85%"),
            # flake8
            MagicMock(returncode=0, stdout="0\n"),
            # bandit
            MagicMock(returncode=0, stdout='{"metrics": {"_totals": {"SEVERITY.HIGH": 0, "SEVERITY.MEDIUM": 0}}, "results": []}')
        ]

        # scan_todos
        mock_scan.return_value = [] # No TODOs

        badges = self.manager.generate_badges()

        self.assertEqual(len(badges), 4)

        # Coverage
        self.assertEqual(badges[0].label, "coverage")
        self.assertEqual(badges[0].message, "85%")
        self.assertEqual(badges[0].color, "green")

        # Lint
        self.assertEqual(badges[1].label, "lint")
        self.assertEqual(badges[1].message, "0 issues")
        self.assertEqual(badges[1].color, "green")

        # Security
        self.assertEqual(badges[2].label, "security")
        self.assertEqual(badges[2].message, "secure")
        self.assertEqual(badges[2].color, "green")

        # TODOs
        self.assertEqual(badges[3].label, "todos")
        self.assertEqual(badges[3].message, "0")
        self.assertEqual(badges[3].color, "green")

    @patch("shared.badges.shutil.which")
    @patch("shared.badges.run_command")
    @patch("shared.badges.scan_todos")
    def test_generate_badges_failures(self, mock_scan, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/tool"

        mock_run.side_effect = [
            # pytest (fail)
            MagicMock(returncode=1, stdout="failures"),
            # flake8 (15 issues)
            MagicMock(returncode=1, stdout="15\n"),
            # bandit (high severity)
            MagicMock(returncode=0, stdout='{"metrics": {}, "results": [{"issue_severity": "HIGH"}]}')
        ]

        # 25 TODOs
        mock_scan.return_value = [{"tag": "TODO"}] * 25

        badges = self.manager.generate_badges()

        self.assertEqual(badges[0].message, "failing")
        self.assertEqual(badges[0].color, "red")

        self.assertEqual(badges[1].message, "15 issues")
        self.assertEqual(badges[1].color, "red")

        self.assertEqual(badges[2].message, "1 high")
        self.assertEqual(badges[2].color, "red")

        self.assertEqual(badges[3].message, "25")
        self.assertEqual(badges[3].color, "orange")

    def test_update_readme_create(self):
        # Mock Path.exists and read_text/write_text
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            result = self.manager.update_readme([])
            self.assertFalse(result)

    def test_update_readme_insert(self):
        badges = [Badge("test", "msg", "green")]
        with patch.object(Path, "exists") as mock_exists, \
             patch.object(Path, "read_text") as mock_read, \
             patch.object(Path, "write_text") as mock_write:

            mock_exists.return_value = True
            mock_read.return_value = "# My Project\nDescription."

            self.manager.update_readme(badges)

            args, _ = mock_write.call_args
            content = args[0]
            self.assertIn("<!-- BADGES_START -->", content)
            self.assertIn("![test](https://img.shields.io/badge/test-msg-green)", content)
            self.assertIn("# My Project", content)

    def test_update_readme_replace(self):
        badges = [Badge("new", "msg", "blue")]
        old_content = """# Title
<!-- BADGES_START -->
old badge
<!-- BADGES_END -->
Body"""

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "read_text", return_value=old_content), \
             patch.object(Path, "write_text") as mock_write:

            self.manager.update_readme(badges)

            args, _ = mock_write.call_args
            content = args[0]
            self.assertIn("![new]", content)
            self.assertNotIn("old badge", content)
