import unittest
import tempfile
import shutil
from pathlib import Path
from shared.pattern_lab import PatternLabManager, TEMPLATES

class TestPatternLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = PatternLabManager()
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_list_patterns(self):
        patterns = self.manager.list_patterns()
        self.assertEqual(patterns, sorted(TEMPLATES.keys()))
        self.assertIn("Singleton", patterns)

    def test_list_languages(self):
        langs = self.manager.list_languages()
        self.assertIn("python", langs)
        self.assertIn("javascript", langs)

    def test_get_template(self):
        code = self.manager.get_template("Singleton", "python")
        self.assertIsNotNone(code)
        self.assertIn("class Singleton", code)

        # Invalid pattern
        self.assertIsNone(self.manager.get_template("Invalid", "python"))
        # Invalid lang
        self.assertIsNone(self.manager.get_template("Singleton", "rust"))

    def test_generate(self):
        output_file = self.test_dir / "singleton.py"
        success = self.manager.generate("Singleton", "python", str(output_file))
        self.assertTrue(success)
        self.assertTrue(output_file.exists())
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("class Singleton", content)

    def test_generate_invalid(self):
        output_file = self.test_dir / "invalid.py"
        success = self.manager.generate("Invalid", "python", str(output_file))
        self.assertFalse(success)
        self.assertFalse(output_file.exists())

if __name__ == "__main__":
    unittest.main()
