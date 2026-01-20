import unittest
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from shared.smart_search import SmartSearchEngine, STOPWORDS, CODE_STOPWORDS

class TestSmartSearchEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        self.engine = SmartSearchEngine(self.project_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_tokenize(self):
        text = "The quick brown fox jumps over the lazy dog! def function(): return True"
        tokens = self.engine._tokenize(text)

        # Check stopwords removal
        self.assertNotIn("the", tokens)
        self.assertNotIn("def", tokens)
        self.assertNotIn("return", tokens)

        # Check tokenization
        self.assertIn("quick", tokens)
        self.assertIn("brown", tokens)
        self.assertIn("fox", tokens)

        # Check case normalization
        self.assertIn("true", tokens)

    def test_indexing_and_search(self):
        # Create some dummy files
        (self.project_dir / "file1.txt").write_text("apple banana cherry")
        (self.project_dir / "file2.txt").write_text("banana date elderberry")
        (self.project_dir / "file3.txt").write_text("apple apple apple") # High frequency of apple

        self.engine.index()

        self.assertEqual(self.engine.num_docs, 3)

        # Test search for "banana"
        results = self.engine.search("banana")
        self.assertEqual(len(results), 2)
        files = {r['file'] for r in results}
        self.assertIn("file1.txt", files)
        self.assertIn("file2.txt", files)

        # Test search for "apple" - file3 should rank higher due to frequency
        results = self.engine.search("apple")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['file'], "file3.txt")
        self.assertEqual(results[1]['file'], "file1.txt")

    def test_search_snippet(self):
        content = """
        This is line one.
        This is line two with special keyword.
        This is line three.
        """
        (self.project_dir / "snippet.txt").write_text(content)
        self.engine.index()

        results = self.engine.search("special keyword")
        self.assertEqual(len(results), 1)
        self.assertIn("special keyword", results[0]['snippet'])
        self.assertIn("line two", results[0]['snippet'])

    def test_empty_search(self):
        (self.project_dir / "test.txt").write_text("some content")
        self.engine.index()

        results = self.engine.search("nonexistentword")
        self.assertEqual(len(results), 0)

    def test_ignore_binary(self):
        # Create a "binary" file (by extension)
        (self.project_dir / "image.png").write_text("some binary content")
        self.engine.index()

        # Should not index .png
        found = any(doc['path'] == "image.png" for doc in self.engine.documents)
        self.assertFalse(found)

if __name__ == "__main__":
    unittest.main()
