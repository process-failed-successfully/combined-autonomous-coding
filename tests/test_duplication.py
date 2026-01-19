import unittest
import tempfile
import shutil
import os
from pathlib import Path
from shared.duplication import tokenize_file, find_duplicates

class TestDuplicationDetector(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, filename, content):
        path = self.test_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def test_tokenize_file(self):
        content = """
        def hello():
            # This is a comment
            print("Hello")
        """
        f = self.create_file("test.py", content)
        tokens = tokenize_file(f)

        # Check we have tokens
        self.assertTrue(len(tokens) > 0)

        # Check comments are ignored
        token_strings = [t[1] for t in tokens]
        self.assertNotIn("# This is a comment", token_strings)
        self.assertIn("def", token_strings)
        self.assertIn("hello", token_strings)
        self.assertIn("print", token_strings)

    def test_find_duplicates_simple(self):
        # Use simple repeated text
        line = "x = 1; y = 2; z = 3\n"
        # 12 tokens per line.
        # 10 lines -> 120 tokens.
        block = line * 10

        content = f"""
        def part1():
            {block}

        def part2():
            print("sep")
            {block}
        """
        f = self.create_file("dup.py", content)

        duplicates = find_duplicates(self.test_dir, min_tokens=20)
        self.assertTrue(len(duplicates) > 0)

        self.assertGreater(duplicates[0]['token_count'], 100)

        # Check locations
        locs = duplicates[0]['locations']
        self.assertEqual(len(locs), 2)
        self.assertEqual(locs[0]['file'], "dup.py")
        self.assertEqual(locs[1]['file'], "dup.py")

    def test_find_duplicates_cross_file(self):
        # Unique content
        lines = [f"x_{i} = {i}" for i in range(50)]
        block = "\n".join(lines)

        self.create_file("file1.py", block)
        self.create_file("file2.py", block)

        duplicates = find_duplicates(self.test_dir, min_tokens=30)
        self.assertTrue(len(duplicates) > 0)
        self.assertEqual(len(duplicates[0]['locations']), 2)

    def test_no_duplicates(self):
        self.create_file("a.py", "x = 1")
        self.create_file("b.py", "y = 2")

        duplicates = find_duplicates(self.test_dir, min_tokens=10)
        self.assertEqual(len(duplicates), 0)

    def test_ignore_pattern(self):
        # Unique content to avoid internal duplication
        lines = [f"ignore_test_{i} = {i}" for i in range(50)]
        block = "\n".join(lines)

        self.create_file("src/file1.py", block)
        self.create_file("ignored/file2.py", block)

        # Should duplicate if not ignored (cross-file)
        dups = find_duplicates(self.test_dir, min_tokens=30)
        self.assertTrue(len(dups) > 0)

        # Should not duplicate if ignored
        dups_ignored = find_duplicates(self.test_dir, ignore_patterns=["ignored/*"], min_tokens=30)

        if len(dups_ignored) > 0:
             print(f"DEBUG: Ignored failed. Found: {dups_ignored}")

        self.assertEqual(len(dups_ignored), 0)

if __name__ == '__main__':
    unittest.main()
