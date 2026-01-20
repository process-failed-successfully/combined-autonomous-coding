import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
from shared.summarize import run_summarize_logic, _get_git_diff_for_summary


class TestSummarize(unittest.IsolatedAsyncioTestCase):
    @patch("shared.summarize.shutil.which")
    @patch("pathlib.Path.is_dir")
    @patch("shared.summarize.subprocess.run")
    def test_get_git_diff_uncommitted(self, mock_run, mock_is_dir, mock_which):
        mock_which.return_value = "/usr/bin/git"
        mock_is_dir.return_value = True

        mock_proc = MagicMock()
        mock_proc.stdout = "diff --git a/file.py b/file.py"
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        result = _get_git_diff_for_summary(Path("."), None)

        self.assertIn("--- Uncommitted Changes ---", result)
        self.assertIn("diff --git", result)
        mock_run.assert_called_with(
            ["/usr/bin/git", "-C", ".", "diff", "HEAD"],
            capture_output=True, text=True, check=True
        )

    @patch("shared.summarize.shutil.which")
    @patch("pathlib.Path.is_dir")
    @patch("shared.summarize.subprocess.run")
    def test_get_git_diff_range(self, mock_run, mock_is_dir, mock_which):
        mock_which.return_value = "/usr/bin/git"
        mock_is_dir.return_value = True

        mock_proc = MagicMock()
        mock_proc.stdout = "diff output"
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        result = _get_git_diff_for_summary(Path("."), "main..HEAD")

        self.assertIn("--- Range main..HEAD ---", result)
        mock_run.assert_called_with(
            ["/usr/bin/git", "-C", ".", "diff", "main..HEAD"],
            capture_output=True, text=True, check=True
        )

    @patch("shared.summarize.shutil.which")
    @patch("pathlib.Path.is_dir")
    @patch("shared.summarize.subprocess.run")
    def test_get_git_diff_commit(self, mock_run, mock_is_dir, mock_which):
        mock_which.return_value = "/usr/bin/git"
        mock_is_dir.return_value = True

        mock_proc = MagicMock()
        mock_proc.stdout = "show output"
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        result = _get_git_diff_for_summary(Path("."), "abcdef")

        self.assertIn("--- Commit abcdef ---", result)
        mock_run.assert_called_with(
            ["/usr/bin/git", "-C", ".", "show", "abcdef"],
            capture_output=True, text=True, check=True
        )

    @patch("shared.summarize.GeminiAgent")
    @patch("shared.summarize._get_git_diff_for_summary")
    async def test_run_summarize_logic(self, mock_get_diff, mock_agent_cls):
        mock_get_diff.return_value = "--- Uncommitted Changes ---\n+ added line"

        mock_agent = AsyncMock()
        mock_agent.run_agent_session.return_value = ("completed", "Summary: Added a line.", [])
        mock_agent_cls.return_value = mock_agent

        result = await run_summarize_logic(
            project_dir=Path("."),
            target=None,
            agent_type="gemini"
        )

        self.assertTrue(result)
        mock_agent.run_agent_session.assert_called_once()
        args, _ = mock_agent.run_agent_session.call_args
        self.assertIn("+ added line", args[0])

    @patch("shared.summarize.GeminiAgent")
    @patch("shared.summarize._get_git_diff_for_summary")
    async def test_run_summarize_logic_no_diff(self, mock_get_diff, mock_agent_cls):
        mock_get_diff.return_value = ""

        result = await run_summarize_logic(
            project_dir=Path("."),
            target=None
        )

        self.assertTrue(result)
        mock_agent_cls.assert_not_called()
