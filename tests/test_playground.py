import unittest
import shutil
from pathlib import Path
from unittest.mock import patch
from shared.playground import PlaygroundManager


class TestPlaygroundManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_playground_project")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.manager = PlaygroundManager(self.test_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_init(self):
        self.assertEqual(self.manager.project_dir, self.test_dir.resolve())
        self.assertEqual(self.manager.playground_dir, self.test_dir.resolve() / ".playground")

    def test_ensure_setup(self):
        self.manager.ensure_setup()
        self.assertTrue(self.manager.playground_dir.exists())
        self.assertTrue(self.manager.playground_dir.is_dir())

        gitignore = self.test_dir / ".gitignore"
        self.assertTrue(gitignore.exists())
        self.assertIn(".playground/", gitignore.read_text())

    def test_create(self):
        file_path = self.manager.create("test_script.py")
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.name, "test_script.py")

        content = file_path.read_text()
        self.assertIn("import os", content)
        self.assertIn("def main():", content)

    def test_create_with_existing_imports(self):
        # Create a dummy python file in project to test import scanning
        (self.test_dir / "src").mkdir()
        (self.test_dir / "src/module.py").write_text("import json\nfrom datetime import datetime")

        file_path = self.manager.create("import_test.py")
        content = file_path.read_text()

        self.assertIn("import json", content)
        self.assertIn("# from datetime import ...", content)

    def test_list_files(self):
        self.manager.ensure_setup()
        (self.manager.playground_dir / "file1.py").touch()
        (self.manager.playground_dir / "file2.py").touch()

        files = self.manager.list_files()
        names = [f.name for f in files]
        self.assertIn("file1.py", names)
        self.assertIn("file2.py", names)

    def test_delete(self):
        self.manager.ensure_setup()
        file_path = self.manager.playground_dir / "to_delete.py"
        file_path.touch()

        self.assertTrue(self.manager.delete("to_delete.py"))
        self.assertFalse(file_path.exists())

        self.assertFalse(self.manager.delete("non_existent.py"))

    @patch("shared.playground.subprocess.run")
    def test_run(self, mock_run):
        self.manager.ensure_setup()
        file_path = self.manager.playground_dir / "run_test.py"
        file_path.touch()

        mock_run.return_value.returncode = 0

        success = self.manager.run("run_test.py")
        self.assertTrue(success)

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0][1], str(file_path))
        self.assertIn("PYTHONPATH", kwargs["env"])


if __name__ == "__main__":
    unittest.main()
