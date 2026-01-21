import unittest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.prune import PruneManager

class TestPruneManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = PruneManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, path, content):
        p = self.test_dir / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def test_scan_unused_dependencies(self):
        # 1. Setup requirements.txt
        self.create_file("requirements.txt", "requests==2.0.0\nPyYAML==5.0\nunused-pkg==1.0\n")

        # 2. Setup python files
        self.create_file("main.py", "import requests\nimport yaml")

        # 3. Mock DependencyAnalyzer
        # We can rely on the real one since we created the file, but let's mock it for stability if needed.
        # Actually, real file parsing is fine.

        # Run scan
        unused = self.manager.scan_unused_dependencies()

        # Expect 'unused-pkg' to be in unused list
        unused_names = [d['name'] for d in unused]
        self.assertIn("unused-pkg", unused_names)
        self.assertNotIn("requests", unused_names)
        self.assertNotIn("PyYAML", unused_names) # Should be mapped to 'yaml'

    def test_scan_unused_files(self):
        # Create structure
        # main.py -> imports utils
        # utils.py
        # unused.py
        # tests/test_main.py (should be ignored by default in prune logic as it's in ignored dir)

        self.create_file("main.py", "import utils\nif __name__ == '__main__': pass")
        self.create_file("utils.py", "def helper(): pass")
        self.create_file("unused.py", "def lonely(): pass")
        self.create_file("tests/test_main.py", "import main")

        # Run scan
        candidates = self.manager.scan_unused_files()
        candidate_names = [f.name for f in candidates]

        self.assertIn("unused.py", candidate_names)
        self.assertNotIn("main.py", candidate_names) # Entry point (if __name__) + explicitly ignored name
        self.assertNotIn("utils.py", candidate_names) # Imported by main
        # tests/test_main.py is in IGNORE_DIRS ("tests") so it shouldn't be returned as a candidate to delete
        self.assertNotIn("test_main.py", candidate_names)

    def test_delete_dependencies(self):
        self.create_file("requirements.txt", "keep-me==1.0\ndelete-me==2.0\n")

        deps_to_delete = [{"name": "delete-me", "version": "2.0"}]
        self.manager._delete_dependencies(deps_to_delete)

        content = (self.test_dir / "requirements.txt").read_text()
        self.assertIn("keep-me==1.0", content)
        self.assertNotIn("delete-me==2.0", content)

    def test_delete_files(self):
        f = self.create_file("todelete.py", "pass")
        self.assertTrue(f.exists())

        self.manager._delete_files([f])
        self.assertFalse(f.exists())

if __name__ == '__main__':
    unittest.main()
