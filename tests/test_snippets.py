import unittest
import shutil
import tempfile
from pathlib import Path
from shared.snippets import SnippetManager

class TestSnippetManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = SnippetManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_create_and_list_snippets(self):
        self.manager.create_snippet("test_snippet", "print('hello')")
        snippets = self.manager.list_snippets()
        self.assertIn("test_snippet", snippets)
        self.assertEqual(len(snippets), 1)

    def test_get_snippet(self):
        content = "def foo(): pass"
        self.manager.create_snippet("foo_func", content)
        retrieved = self.manager.get_snippet("foo_func")
        self.assertEqual(retrieved, content)

    def test_get_nonexistent_snippet(self):
        retrieved = self.manager.get_snippet("nonexistent")
        self.assertIsNone(retrieved)

    def test_delete_snippet(self):
        self.manager.create_snippet("to_delete", "content")
        self.assertTrue(self.manager.delete_snippet("to_delete"))
        self.assertFalse(self.manager.delete_snippet("to_delete"))
        self.assertNotIn("to_delete", self.manager.list_snippets())

    def test_apply_snippet_append(self):
        target = self.test_dir / "target.py"
        target.write_text("line1\n")

        self.manager.create_snippet("snip", "line2")
        self.manager.apply_snippet("snip", target, mode="append")

        content = target.read_text()
        self.assertEqual(content, "line1\nline2")

    def test_apply_snippet_prepend(self):
        target = self.test_dir / "target.py"
        target.write_text("line2")

        self.manager.create_snippet("snip", "line1")
        self.manager.apply_snippet("snip", target, mode="prepend")

        content = target.read_text()
        self.assertEqual(content, "line1\nline2")

    def test_apply_snippet_overwrite(self):
        target = self.test_dir / "target.py"
        target.write_text("old content")

        self.manager.create_snippet("snip", "new content")
        self.manager.apply_snippet("snip", target, mode="overwrite")

        content = target.read_text()
        self.assertEqual(content, "new content")

    def test_apply_snippet_new_file(self):
        target = self.test_dir / "new_file.py"
        self.manager.create_snippet("snip", "content")
        self.manager.apply_snippet("snip", target)

        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(), "content")

if __name__ == "__main__":
    unittest.main()
