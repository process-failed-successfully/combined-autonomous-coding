import unittest
from unittest.mock import patch, AsyncMock
from pathlib import Path
import subprocess
from shared.ai_git import generate_commit_message_logic


class TestAiGit(unittest.IsolatedAsyncioTestCase):

    @patch("shared.ai_git.shutil.which")
    @patch("shared.ai_git.subprocess.run")
    @patch("shared.ai_git.GeminiAgent")
    async def test_generate_commit_message_logic(self, mock_gemini_agent_class, mock_run, mock_which):
        # Setup mocks
        mock_which.return_value = "/usr/bin/git"

        # Mock git diff --cached output
        mock_run.return_value.stdout = "diff --git a/file.txt b/file.txt\n+added line"
        mock_run.return_value.returncode = 0

        # Mock agent
        mock_agent_instance = AsyncMock()
        mock_gemini_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run_agent_session.return_value = (True, "feat: add line to file.txt", [])

        project_dir = Path("/tmp/project")

        # Mock Path.is_dir
        with patch.object(Path, 'is_dir', return_value=True):
            # Run
            msg = await generate_commit_message_logic(project_dir)

        # Assertions
        self.assertEqual(msg, "feat: add line to file.txt")
        mock_run.assert_called_with(
            ["/usr/bin/git", "-C", str(project_dir), "diff", "--cached"],
            capture_output=True, text=True, check=True
        )
        mock_agent_instance.run_agent_session.assert_called_once()

    @patch("shared.ai_git.shutil.which")
    @patch("shared.ai_git.subprocess.run")
    async def test_generate_commit_message_empty_diff(self, mock_run, mock_which):
        # Setup mocks
        mock_which.return_value = "/usr/bin/git"

        # Mock git diff --cached output (empty)
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        project_dir = Path("/tmp/project")

        # Mock Path.is_dir
        with patch.object(Path, 'is_dir', return_value=True):
            # Run
            msg = await generate_commit_message_logic(project_dir)

        # Assertions
        self.assertIsNone(msg)

    @patch("shared.ai_git.shutil.which")
    @patch("shared.ai_git.subprocess.run")
    async def test_generate_commit_message_git_error(self, mock_run, mock_which):
        # Setup mocks
        mock_which.return_value = "/usr/bin/git"

        # Mock git error
        mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "diff"])

        project_dir = Path("/tmp/project")

        # Mock Path.is_dir
        with patch.object(Path, 'is_dir', return_value=True):
            # Run
            msg = await generate_commit_message_logic(project_dir)

        # Assertions
        self.assertIsNone(msg)

    @patch("shared.ai_git.shutil.which")
    @patch("shared.ai_git.subprocess.run")
    @patch("shared.ai_git.GeminiAgent")
    async def test_generate_commit_message_agent_error(self, mock_gemini_agent_class, mock_run, mock_which):
        # Setup mocks
        mock_which.return_value = "/usr/bin/git"
        mock_run.return_value.stdout = "diff..."

        # Mock agent error
        mock_agent_instance = AsyncMock()
        mock_gemini_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run_agent_session.side_effect = Exception("Agent Error")

        project_dir = Path("/tmp/project")

        # Mock Path.is_dir
        with patch.object(Path, 'is_dir', return_value=True):
            # Run
            msg = await generate_commit_message_logic(project_dir)

        # Assertions
        self.assertIsNone(msg)


if __name__ == "__main__":
    unittest.main()
