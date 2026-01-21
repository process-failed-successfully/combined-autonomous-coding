import unittest
import shutil
import tempfile
import sys
import os
from pathlib import Path

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.scaffold import ScaffoldManager, TEMPLATES

class TestScaffoldManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = ScaffoldManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_list_templates(self):
        templates = self.manager.list_templates()
        self.assertEqual(len(templates), len(TEMPLATES))
        self.assertIn("python-basic", templates)

    def test_scaffold_basic(self):
        success = self.manager.scaffold("python-basic")
        self.assertTrue(success)
        self.assertTrue((self.test_dir / "main.py").exists())
        self.assertTrue((self.test_dir / "README.md").exists())

        # Check content
        content = (self.test_dir / "main.py").read_text()
        self.assertIn("Hello, World!", content)

    def test_scaffold_unknown_template(self):
        success = self.manager.scaffold("non-existent-template")
        self.assertFalse(success)

    def test_scaffold_existing_files_no_force(self):
        # Create a file that conflicts
        (self.test_dir / "main.py").touch()

        success = self.manager.scaffold("python-basic")
        self.assertFalse(success)

    def test_scaffold_existing_files_force(self):
        # Create a file that conflicts
        (self.test_dir / "main.py").write_text("old content")

        success = self.manager.scaffold("python-basic", force=True)
        self.assertTrue(success)

        content = (self.test_dir / "main.py").read_text()
        self.assertNotEqual(content, "old content")
        self.assertIn("Hello, World!", content)

    def test_scaffold_subdirectory(self):
        sub_dir = self.test_dir / "my_project"
        manager = ScaffoldManager(sub_dir)
        success = manager.scaffold("python-basic")
        self.assertTrue(success)
        self.assertTrue((sub_dir / "main.py").exists())

    def test_git_init(self):
        # Mocking git call would be better, but integration test is fine here
        # We need to make sure 'git' is available, or skip
        if not shutil.which("git"):
            return

        success = self.manager.scaffold("python-basic")
        self.assertTrue(success)
        self.assertTrue((self.test_dir / ".git").exists())

if __name__ == "__main__":
    unittest.main()
