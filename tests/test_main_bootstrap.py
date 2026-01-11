import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import shutil
import sys
import os
from io import StringIO

# This is a bit of a hack to make sure we can import from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_bootstrap

class TestBootstrapCommand(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_bootstrap_project")
        self.templates_dir = Path("templates")
        # Clean up any previous test runs
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('sys.stdout', new_callable=StringIO)
    def test_list_templates(self, mock_stdout):
        args = MagicMock()
        args.list = True
        with self.assertRaises(SystemExit) as cm:
            run_bootstrap(args)
        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("python-flask-basic", output)
        self.assertIn("react-vite-ts", output)

    def test_bootstrap_project_creation(self):
        args = MagicMock()
        args.list = False
        args.template = "python-flask-basic"
        args.project_dir = self.test_dir

        with self.assertRaises(SystemExit) as cm:
            run_bootstrap(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify that the project directory and its contents were created
        self.assertTrue(self.test_dir.exists())
        self.assertTrue((self.test_dir / "app.py").exists())
        self.assertTrue((self.test_dir / "requirements.txt").exists())
        self.assertTrue((self.test_dir / ".git").exists())
        self.assertTrue((self.test_dir / "app_spec.txt").exists())
        with open(self.test_dir / "app_spec.txt", "r") as f:
            content = f.read()
            self.assertIn("python-flask-basic", content)

    def test_bootstrap_fails_if_dir_not_empty(self):
        self.test_dir.mkdir()
        (self.test_dir / "some_file.txt").touch()
        args = MagicMock()
        args.list = False
        args.template = "python-flask-basic"
        args.project_dir = self.test_dir

        with self.assertRaises(SystemExit) as cm:
            run_bootstrap(args)
        self.assertEqual(cm.exception.code, 1)

    def test_bootstrap_fails_if_template_not_found(self):
        args = MagicMock()
        args.list = False
        args.template = "non-existent-template"
        args.project_dir = self.test_dir

        with self.assertRaises(SystemExit) as cm:
            run_bootstrap(args)
        self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
