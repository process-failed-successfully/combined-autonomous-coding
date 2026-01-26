import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import tempfile
import shutil
import subprocess
from io import StringIO
import contextlib
import sys

# Add the parent directory to the path to allow imports from 'shared'
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_init

class TestMainInit(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)
        # We need to create a dummy main.py for executable_name to work
        (self.project_dir / "main.py").touch()
        # Mock sys.argv
        self.argv_patch = patch('sys.argv', [str(self.project_dir / "main.py")])
        self.argv_patch.start()


    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        self.argv_patch.stop()

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('subprocess.run')
    @patch('builtins.input', side_effect=['y', 'y', 'This is the spec.', '', ''])
    def test_run_init_happy_path(self, mock_input, mock_subprocess_run, mock_which):
        """Tests the full, successful interactive setup for a new project."""
        args = MagicMock(project_dir=self.project_dir, yes=False)
        output = StringIO()

        with contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as cm:
                run_init(args)

        self.assertEqual(cm.exception.code, 0)

        # Verify git initialization was called
        mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', 'init', '-b', 'main', str(self.project_dir)],
            check=True, capture_output=True
        )

        # Verify .gitignore was created
        gitignore_path = self.project_dir / ".gitignore"
        self.assertTrue(gitignore_path.exists())
        content = gitignore_path.read_text()
        self.assertIn("__pycache__/", content)
        self.assertIn(".agent_trash/", content)
        # Security checks
        self.assertIn(".agent_secrets.key", content)
        self.assertIn(".agent_secrets.enc", content)
        self.assertIn("agent_config.yaml", content)

        # Verify app_spec.txt was created with correct content
        spec_path = self.project_dir / "app_spec.txt"
        self.assertTrue(spec_path.exists())
        self.assertEqual(spec_path.read_text(), "This is the spec.")

        # Check output for key messages
        stdout = output.getvalue()
        self.assertIn("Successfully initialized a new Git repository.", stdout)
        self.assertIn("Created a .gitignore file.", stdout)
        self.assertIn("Saved application specification to app_spec.txt", stdout)
        self.assertIn("Project initialization complete!", stdout)

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('subprocess.run')
    @patch('builtins.input', side_effect=['n', 'n'])
    def test_run_init_user_says_no(self, mock_input, mock_subprocess_run, mock_which):
        """Tests that declining git and gitignore setup works as expected."""
        args = MagicMock(project_dir=self.project_dir, yes=False)
        output = StringIO()

        # Mock spec input to be empty to exit that stage quickly
        with patch('builtins.input', side_effect=['n', 'n', '', '']):
            with contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit):
                    run_init(args)

        # Verify git was NOT called
        mock_subprocess_run.assert_not_called()

        # Verify .gitignore was NOT created
        self.assertFalse((self.project_dir / ".gitignore").exists())

        # Verify app_spec.txt was NOT created
        self.assertFalse((self.project_dir / "app_spec.txt").exists())

        stdout = output.getvalue()
        self.assertNotIn("Successfully initialized a new Git repository.", stdout)
        self.assertNotIn("Created a .gitignore file.", stdout)

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('subprocess.run')
    def test_run_init_non_interactive_yes_flag(self, mock_subprocess_run, mock_which):
        """Tests that the --yes flag creates git and gitignore without prompts."""
        args = MagicMock(project_dir=self.project_dir, yes=True)
        output = StringIO()

        # Mock spec creation to be empty to avoid input() call
        with patch('builtins.input', side_effect=['', '']):
            with contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit):
                    run_init(args)

        # Verify git initialization was called
        mock_subprocess_run.assert_called_once()
        # Verify .gitignore was created
        self.assertTrue((self.project_dir / ".gitignore").exists())

    def test_run_init_existing_files(self):
        """Tests behavior when git, gitignore, and spec already exist."""
        # Setup existing files
        (self.project_dir / ".git").mkdir()
        (self.project_dir / ".gitignore").write_text("existing_ignore")
        (self.project_dir / "app_spec.txt").write_text("existing_spec")

        args = MagicMock(project_dir=self.project_dir, yes=False)
        output = StringIO()

        # 'n' to not overwrite spec, then empty input to finish spec entry
        with patch('builtins.input', side_effect=['n', '', '']):
            with contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit):
                    run_init(args)

        # Verify original files are untouched
        self.assertEqual((self.project_dir / ".gitignore").read_text(), "existing_ignore")
        self.assertEqual((self.project_dir / "app_spec.txt").read_text(), "existing_spec")

        stdout = output.getvalue()
        self.assertIn("Git repository already exists.", stdout)
        self.assertIn(".gitignore file already exists.", stdout)
        self.assertIn("Application spec file already exists: app_spec.txt", stdout)
        self.assertNotIn("Successfully initialized", stdout)
        self.assertNotIn("Created a .gitignore", stdout)

    @patch('builtins.input', side_effect=['y', 'new spec content', '', ''])
    def test_run_init_overwrite_spec(self, mock_input):
        """Tests overwriting an existing app_spec.txt."""
        (self.project_dir / "app_spec.txt").write_text("old spec")
        args = MagicMock(project_dir=self.project_dir, yes=False)

        # We don't care about git/gitignore for this test, so let's mock them as existing
        (self.project_dir / ".git").mkdir()
        (self.project_dir / ".gitignore").touch()

        with self.assertRaises(SystemExit):
            run_init(args)

        self.assertEqual((self.project_dir / "app_spec.txt").read_text(), "new spec content")

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'git init', stderr=b'fatal error'))
    def test_run_init_git_init_fails(self, mock_subprocess_run, mock_which):
        """Tests that a git init failure is handled gracefully."""
        args = MagicMock(project_dir=self.project_dir, yes=True) # Use yes to skip input
        output = StringIO()

        with patch('builtins.input', side_effect=['', '']): # Skip spec
            with contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit):
                    run_init(args)

        stdout = output.getvalue()
        self.assertIn("Error initializing Git repository: fatal error", stdout)

if __name__ == '__main__':
    unittest.main()