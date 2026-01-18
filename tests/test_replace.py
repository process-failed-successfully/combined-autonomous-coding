import unittest
import shutil
import tempfile
from pathlib import Path
from shared.replace import replace_in_codebase

class TestReplace(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)

        # Create some test files
        (self.root / "file1.txt").write_text("Hello World\nThis is a test.\nFoo Bar")
        (self.root / "file2.txt").write_text("Another file.\nHello there.\nBaz Qux")
        (self.root / "file3.py").write_text("def hello():\n    print('Hello World')")

        # Create a nested directory
        (self.root / "subdir").mkdir()
        (self.root / "subdir/file4.md").write_text("# Hello World\nDocumentation")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_literal_replace(self):
        # Replace "Hello" with "Hi"
        stats = replace_in_codebase(
            project_dir=self.root,
            pattern="Hello",
            replacement="Hi",
            case_sensitive=True
        )

        self.assertEqual(stats["files_changed"], 4)
        self.assertEqual(stats["replacements_count"], 4)

        # Verify content
        self.assertEqual((self.root / "file1.txt").read_text(), "Hi World\nThis is a test.\nFoo Bar")
        self.assertEqual((self.root / "file3.py").read_text(), "def hello():\n    print('Hi World')")

    def test_case_insensitive_replace(self):
        # Replace "hello" with "Greetings" (case insensitive)
        stats = replace_in_codebase(
            project_dir=self.root,
            pattern="hello",
            replacement="Greetings",
            case_sensitive=False
        )

        # Matches:
        # file1.txt: Hello -> Greetings
        # file2.txt: Hello -> Greetings
        # file3.py: hello -> Greetings, Hello -> Greetings
        # subdir/file4.md: Hello -> Greetings

        self.assertEqual(stats["files_changed"], 4)
        self.assertEqual(stats["replacements_count"], 5)

        self.assertIn("Greetings World", (self.root / "file1.txt").read_text())
        self.assertIn("def Greetings():", (self.root / "file3.py").read_text())

    def test_regex_replace(self):
        # Replace "Foo|Baz" with "Metasyntactic"
        stats = replace_in_codebase(
            project_dir=self.root,
            pattern="Foo|Baz",
            replacement="Metasyntactic",
            is_regex=True
        )

        self.assertEqual(stats["files_changed"], 2) # file1 and file2
        self.assertIn("Metasyntactic Bar", (self.root / "file1.txt").read_text())
        self.assertIn("Metasyntactic Qux", (self.root / "file2.txt").read_text())

    def test_regex_group_replace(self):
        # Swap words: "Baz Qux" -> "Qux Baz"
        stats = replace_in_codebase(
            project_dir=self.root,
            pattern=r"(Baz) (Qux)",
            replacement=r"\2 \1",
            is_regex=True
        )

        self.assertEqual(stats["files_changed"], 1) # file2
        self.assertIn("Qux Baz", (self.root / "file2.txt").read_text())

    def test_file_filter(self):
        # Replace "Hello" with "Hi" only in *.py files
        stats = replace_in_codebase(
            project_dir=self.root,
            pattern="Hello",
            replacement="Hi",
            file_pattern="*.py",
            case_sensitive=True
        )

        self.assertEqual(stats["files_changed"], 1)
        self.assertEqual(stats["replacements_count"], 1)
        self.assertIn("Hi World", (self.root / "file3.py").read_text())
        # file1.txt should be unchanged
        self.assertIn("Hello World", (self.root / "file1.txt").read_text())

    def test_dry_run(self):
        # Dry run replacement
        stats = replace_in_codebase(
            project_dir=self.root,
            pattern="Hello",
            replacement="Hi",
            dry_run=True
        )

        self.assertEqual(stats["files_changed"], 4)
        self.assertTrue(len(stats["diffs"]) == 4)

        # Verify files NOT changed
        self.assertIn("Hello World", (self.root / "file1.txt").read_text())

    def test_no_matches(self):
        stats = replace_in_codebase(
            project_dir=self.root,
            pattern="NonExistent",
            replacement="Nothing"
        )
        self.assertEqual(stats["files_changed"], 0)
        self.assertEqual(stats["replacements_count"], 0)

if __name__ == '__main__':
    unittest.main()
