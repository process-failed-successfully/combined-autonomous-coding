import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
from shared.code_review import run_code_review_logic


class TestCodeReview(unittest.IsolatedAsyncioTestCase):
    @patch("shared.code_review.GeminiAgent")
    @patch("shared.code_review.subprocess.run")
    @patch("shared.code_review.Path.exists")
    @patch("shared.code_review.Path.is_file")
    @patch("shared.code_review.Path.read_text")
    async def test_code_review_files(self, mock_read, mock_is_file, mock_exists, mock_run, mock_agent_cls):
        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.run_agent_session.return_value = ("completed", "LGTM", [])
        mock_agent_cls.return_value = mock_agent

        # Mock file system
        # Note: We need to handle when Path(project_dir / file) is called.
        # But for simplicity, we mock Path methods which are called on instances.
        # However, Path instantiation is hard to mock directly without side effects.
        # A simpler way is to integration test or trust file ops.
        # But we can assume 'exists' returns true for our dummy file.

        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_read.return_value = "print('hello')"

        # Run
        result = await run_code_review_logic(
            project_dir=Path("."),
            files=["test.py"],
            agent_type="gemini"
        )

        self.assertTrue(result)
        mock_agent.run_agent_session.assert_called_once()
        args, _ = mock_agent.run_agent_session.call_args
        self.assertIn("print('hello')", args[0])

    @patch("shared.code_review.GeminiAgent")
    @patch("shared.code_review.subprocess.run")
    @patch("shared.code_review.shutil.which")
    @patch("pathlib.Path.is_dir")
    async def test_code_review_diff(self, mock_is_dir, mock_which, mock_run, mock_agent_cls):
        # Mock git existence
        mock_which.return_value = "/usr/bin/git"
        mock_is_dir.return_value = True

        # Mock git output
        mock_proc = MagicMock()
        mock_proc.stdout = "+ print('hello')"
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.run_agent_session.return_value = ("completed", "LGTM", [])
        mock_agent_cls.return_value = mock_agent

        # Run
        result = await run_code_review_logic(
            project_dir=Path("."),
            diff=True,
            agent_type="gemini"
        )

        self.assertTrue(result)
        mock_agent.run_agent_session.assert_called_once()
        args, _ = mock_agent.run_agent_session.call_args
        self.assertIn("+ print('hello')", args[0])
