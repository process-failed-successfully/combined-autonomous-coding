
import unittest
import tempfile
import shutil
from pathlib import Path
from shared.utils import execute_search_block


class TestSearchExclusions(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Create ignored dir with a match
        (self.project_dir / "node_modules").mkdir()
        (self.project_dir / "node_modules" / "bad.js").write_text("target_keyword")

        # Create normal dir with a match
        (self.project_dir / "src").mkdir()
        (self.project_dir / "src" / "good.py").write_text("target_keyword")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    async def test_search_excludes_ignored_dirs(self):
        # We expect execute_search_block to return results from src but NOT node_modules
        # Currently (before fix), it will return BOTH.
        result = await execute_search_block("target_keyword", self.project_dir)

        # Must find the good file
        self.assertIn("src/good.py", result)

        # Must NOT find the bad file (this will fail until fixed)
        self.assertNotIn("node_modules/bad.js", result)


if __name__ == "__main__":
    unittest.main()
