import unittest
import shutil
import tempfile
from pathlib import Path
from shared.stats_lab import CodeStatsManager

class TestCodeStatsManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = CodeStatsManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_python_stats(self):
        code = """
# This is a comment
def foo():
    print("bar")

# Another comment
"""
        (self.test_dir / "test.py").write_text(code)

        stats = self.manager.scan()
        self.assertIn("Python", stats)
        py_stats = stats["Python"]
        self.assertEqual(py_stats["files"], 1)
        self.assertEqual(py_stats["lines"], 6)
        self.assertEqual(py_stats["code"], 2)
        self.assertEqual(py_stats["comment"], 2)
        self.assertEqual(py_stats["blank"], 2)

    def test_javascript_stats(self):
        code = """
// Single line comment
function test() {
    /* Block comment
       across lines */
    console.log("hello");
}
"""
        (self.test_dir / "test.js").write_text(code)

        stats = self.manager.scan()
        self.assertIn("JavaScript", stats)
        js_stats = stats["JavaScript"]
        self.assertEqual(js_stats["files"], 1)
        # 1. Blank
        # 2. // Comment
        # 3. Code (function)
        # 4. Comment (start /*) -> logic treats this as comment if startswith /*
        # 5. Comment (middle)
        # 6. Comment (end */) -> logic treats this as comment
        # 7. Code (console.log)
        # 8. Code (})

        # My naive parser:
        # 1. Blank -> blank+=1
        # 2. // -> comment+=1
        # 3. function -> code+=1
        # 4. /* -> in_block=True, comment+=1
        # 5. across -> in_block=True, comment+=1
        # 6. */ -> comment+=1, in_block=False (because */ in stripped)
        # 7. console -> code+=1
        # 8. } -> code+=1

        # Total lines: 7 (plus empty start/end if docstring behavior varies, but strip handles it?)
        # Actually docstring includes first \n usually.

        self.assertEqual(js_stats["code"], 3)
        self.assertEqual(js_stats["comment"], 3)
        self.assertEqual(js_stats["blank"], 1)

    def test_mixed_languages(self):
        (self.test_dir / "main.py").touch()
        (self.test_dir / "app.js").touch()
        (self.test_dir / "styles.css").touch()
        (self.test_dir / "readme.md").touch()

        stats = self.manager.scan()
        self.assertIn("Python", stats)
        self.assertIn("JavaScript", stats)
        self.assertIn("CSS", stats)
        self.assertIn("Markdown", stats)

        self.assertEqual(stats["Python"]["files"], 1)
        self.assertEqual(stats["JavaScript"]["files"], 1)

    def test_stats_with_exclude(self):
        # Create src/
        src_dir = self.test_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").touch()

        # Create node_modules/
        nm_dir = self.test_dir / "node_modules"
        nm_dir.mkdir()
        (nm_dir / "index.js").touch()

        # Test without exclude
        manager_no_exclude = CodeStatsManager(self.test_dir)
        stats_no_exclude = manager_no_exclude.scan()
        self.assertIn("Python", stats_no_exclude)
        self.assertIn("JavaScript", stats_no_exclude)

        # Test with exclude
        manager_with_exclude = CodeStatsManager(self.test_dir, exclude=["node_modules"])
        stats_with_exclude = manager_with_exclude.scan()
        self.assertIn("Python", stats_with_exclude)
        self.assertNotIn("JavaScript", stats_with_exclude)

if __name__ == "__main__":
    unittest.main()
