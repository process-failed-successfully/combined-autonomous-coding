import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil
import subprocess

from shared.gitignore_lab import GitignoreManager, TEMPLATES

class TestGitignoreLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.manager = GitignoreManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_list_templates(self):
        templates = self.manager.list_templates()
        self.assertIn("python", templates)
        self.assertIn("node", templates)
        self.assertEqual(len(templates), len(TEMPLATES))

    def test_get_template(self):
        content = self.manager.get_template("python")
        self.assertIn("__pycache__", content)

        content = self.manager.get_template("UNKNOWN")
        self.assertIsNone(content)

    def test_generate_single(self):
        content = self.manager.generate(["python"])
        self.assertIn("__pycache__", content)
        self.assertNotIn("node_modules", content)

    def test_generate_multiple(self):
        content = self.manager.generate(["python", "node"])
        self.assertIn("__pycache__", content)
        self.assertIn("node_modules", content)

    def test_generate_unknown(self):
        content = self.manager.generate(["python", "UNKNOWN"])
        self.assertIn("__pycache__", content)
        self.assertIn("Warning: Template 'UNKNOWN' not found", content)

    @patch("subprocess.run")
    def test_check_ignore_ignored(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ".gitignore:1:*.pyc test.pyc"
        mock_run.return_value = mock_result

        result = self.manager.check_ignore("test.pyc")
        self.assertEqual(result["ignored"], "yes")
        self.assertIn("is ignored", result["message"])

    @patch("subprocess.run")
    def test_check_ignore_not_ignored(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = self.manager.check_ignore("test.py")
        self.assertEqual(result["ignored"], "no")
        self.assertIn("is NOT ignored", result["message"])

    @patch("subprocess.run")
    def test_check_ignore_error(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stderr = "fatal: not a git repository"
        mock_run.return_value = mock_result

        result = self.manager.check_ignore("test.py")
        self.assertEqual(result["ignored"], "error")
        self.assertIn("fatal: not a git repository", result["message"])

    def test_append_create_new(self):
        gitignore_path = self.project_dir / ".gitignore"
        self.assertFalse(gitignore_path.exists())

        success = self.manager.append(["python"])
        self.assertTrue(success)
        self.assertTrue(gitignore_path.exists())
        content = gitignore_path.read_text()
        self.assertIn("__pycache__", content)

    def test_append_existing(self):
        gitignore_path = self.project_dir / ".gitignore"
        gitignore_path.write_text("# Existing\n")

        success = self.manager.append(["node"])
        self.assertTrue(success)
        content = gitignore_path.read_text()
        self.assertIn("# Existing", content)
        self.assertIn("node_modules", content)

if __name__ == '__main__':
    unittest.main()
