import unittest
from unittest.mock import patch
from pathlib import Path
import sys
import io
import main


class Args:
    def __init__(self, pattern, replacement, files=None, case_sensitive=False, regex=False, dry_run=False, project_dir=Path(".")):
        self.pattern = pattern
        self.replacement = replacement
        self.files = files
        self.case_sensitive = case_sensitive
        self.regex = regex
        self.dry_run = dry_run
        self.project_dir = project_dir


class TestMainReplace(unittest.TestCase):
    def setUp(self):
        self.captured_output = io.StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("shared.replace.replace_in_codebase")
    def test_run_replace_success(self, mock_replace):
        # Mock return value
        mock_replace.return_value = {
            "files_matched": 2,
            "files_changed": 2,
            "replacements_count": 5,
            "diffs": {"file1.py": "diff content"}
        }

        args = Args(pattern="old", replacement="new")
        with self.assertRaises(SystemExit) as cm:
            main.run_replace(args)

        self.assertEqual(cm.exception.code, 0)

        output = self.captured_output.getvalue()
        self.assertIn("Matched files: 2", output)
        self.assertIn("Files changed: 2", output)
        self.assertIn("Replacements:  5", output)
        self.assertIn("diff content", output)

        mock_replace.assert_called_once_with(
            Path(".").resolve(),
            "old",
            "new",
            file_pattern=None,
            case_sensitive=False,
            is_regex=False,
            dry_run=False
        )

    @patch("shared.replace.replace_in_codebase")
    def test_run_replace_dry_run(self, mock_replace):
        mock_replace.return_value = {
            "files_matched": 1,
            "files_changed": 1,
            "replacements_count": 1,
            "diffs": {"file1.py": "diff content"}
        }

        args = Args(pattern="old", replacement="new", dry_run=True)
        with self.assertRaises(SystemExit) as cm:
            main.run_replace(args)

        self.assertEqual(cm.exception.code, 0)
        output = self.captured_output.getvalue()
        self.assertIn("(Dry Run - No changes will be saved)", output)
        self.assertIn("To apply these changes, run the command again without --dry-run", output)

        mock_replace.assert_called_once_with(
            Path(".").resolve(),
            "old",
            "new",
            file_pattern=None,
            case_sensitive=False,
            is_regex=False,
            dry_run=True
        )

    @patch("shared.replace.replace_in_codebase")
    def test_run_replace_error(self, mock_replace):
        mock_replace.side_effect = Exception("Something went wrong")

        args = Args(pattern="old", replacement="new")
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new=io.StringIO()) as fake_stderr:
                main.run_replace(args)
                self.assertIn("Error during replace: Something went wrong", fake_stderr.getvalue())

        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
