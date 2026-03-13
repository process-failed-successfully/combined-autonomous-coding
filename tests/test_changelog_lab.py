import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import sys
import datetime

from shared.changelog_lab import ChangelogManager, run_changelog_lab_logic

class TestChangelogLab(unittest.TestCase):

    def setUp(self):
        self.manager = ChangelogManager(Path("/fake/project"))

    @patch("shared.changelog_lab.subprocess.run")
    def test_get_commits(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "a1b2c3d|Author|2023-01-01|feat: add awesome feature\ne4f5g6h|Author|2023-01-02|fix: resolve crash\n"
        mock_run.return_value = mock_result

        commits = self.manager.get_commits("main", "HEAD")
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0]['hash'], "a1b2c3d")
        self.assertEqual(commits[0]['message'], "feat: add awesome feature")
        self.assertEqual(commits[1]['hash'], "e4f5g6h")
        self.assertEqual(commits[1]['message'], "fix: resolve crash")

        mock_run.assert_called_once_with(
            ["git", "-C", "/fake/project", "log", "--pretty=format:%h|%an|%ad|%s", "--date=short", "main..HEAD"],
            capture_output=True, text=True, check=True
        )

    def test_parse_commit_message(self):
        ctype, msg = self.manager.parse_commit_message("feat(cli): add colorful output")
        self.assertEqual(ctype, "feat")
        self.assertEqual(msg, "add colorful output")

        ctype, msg = self.manager.parse_commit_message("fix: resolve bug")
        self.assertEqual(ctype, "fix")
        self.assertEqual(msg, "resolve bug")

        ctype, msg = self.manager.parse_commit_message("Initial commit without convention")
        self.assertEqual(ctype, "other")
        self.assertEqual(msg, "Initial commit without convention")

    @patch("shared.changelog_lab.ChangelogManager.get_commits")
    def test_generate_changelog(self, mock_get_commits):
        mock_get_commits.return_value = [
            {'hash': 'a1b2c3d', 'author': 'Dev1', 'date': '2023-01-01', 'message': 'feat: add feature'},
            {'hash': 'e4f5g6h', 'author': 'Dev2', 'date': '2023-01-02', 'message': 'fix: fix bug'},
            {'hash': 'i7j8k9l', 'author': 'Dev3', 'date': '2023-01-03', 'message': 'docs: update readme'},
            {'hash': 'm1n2o3p', 'author': 'Dev4', 'date': '2023-01-04', 'message': 'chore: update deps'},
            {'hash': 'q4r5s6t', 'author': 'Dev5', 'date': '2023-01-05', 'message': 'Random commit'}
        ]

        changelog = self.manager.generate_changelog("main", "HEAD", "1.1.0")
        today = datetime.date.today().isoformat()

        self.assertIn(f"# v1.1.0 ({today})", changelog)
        self.assertIn("## ✨ Features", changelog)
        self.assertIn("- add feature (`a1b2c3d` by Dev1)", changelog)
        self.assertIn("## 🐛 Bug Fixes", changelog)
        self.assertIn("- fix bug (`e4f5g6h` by Dev2)", changelog)
        self.assertIn("## 📚 Documentation", changelog)
        self.assertIn("- update readme (`i7j8k9l` by Dev3)", changelog)
        self.assertIn("## 🧹 Chores", changelog)
        self.assertIn("- update deps (`m1n2o3p` by Dev4)", changelog)
        self.assertIn("## 📦 Other Changes", changelog)
        self.assertIn("- Random commit (`q4r5s6t` by Dev5)", changelog)

    @patch("shared.changelog_lab.ChangelogManager.generate_changelog")
    @patch("builtins.print")
    def test_run_changelog_lab_logic_generate(self, mock_print, mock_generate):
        mock_generate.return_value = "# Changelog"
        args = argparse.Namespace(action="generate", base="v1.0.0", head="HEAD", version="v1.1.0", output=None, tui=False)
        result = run_changelog_lab_logic(args)
        self.assertTrue(result)
        mock_print.assert_called_with("# Changelog")

if __name__ == '__main__':
    unittest.main()
