import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import os
import shutil

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # noqa: E402

from shared.search import search_codebase, _parse_git_grep_output

class TestSearch(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_search_project")
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    def test_parse_git_grep_output_no_context(self):
        output = "file1.py:10:match line\nfile2.js:5:another match"
        results = _parse_git_grep_output(output, context_lines=0)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['file'], "file1.py")
        self.assertEqual(results[0]['line'], 10)
        self.assertEqual(results[0]['content'], "match line")

    def test_parse_git_grep_output_with_context(self):
        # file-1-ctx1
        # file:2:match
        # file-3-ctx2
        output = "f.py-1-ctx1\nf.py:2:match\nf.py-3-ctx2"
        results = _parse_git_grep_output(output, context_lines=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['content'], "match")
        self.assertEqual(results[0]['context_before'], ["1: ctx1"])
        self.assertEqual(results[0]['context_after'], ["3: ctx2"])

    def test_parse_git_grep_complex_context(self):
        # 1-ctx
        # 2:match1
        # 3:match2
        # 4-ctx
        output = "f.py-1-ctx\nf.py:2:match1\nf.py:3:match2\nf.py-4-ctx"
        results = _parse_git_grep_output(output, context_lines=1)

        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]['content'], "match1")
        self.assertEqual(results[0]['context_before'], ["1: ctx"])
        # In my logic, match2 is effectively context_after for match1 if they are in same block
        self.assertIn("3: match2", results[0]['context_after'])

        self.assertEqual(results[1]['content'], "match2")
        self.assertIn("2: match1", results[1]['context_before'])
        self.assertEqual(results[1]['context_after'], ["4: ctx"])

    @patch("shared.search.subprocess.run")
    @patch("shared.search.shutil.which")
    def test_search_git_grep(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/git"
        (self.project_dir / ".git").mkdir()

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "main.py:10:import os"
        mock_run.return_value = mock_process

        results = search_codebase(self.project_dir, "import os", use_git_grep=True)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['file'], "main.py")

        # Check if git grep arguments were correct
        args = mock_run.call_args[0][0]
        self.assertIn("grep", args)
        self.assertIn("import os", args)

    def test_search_python_fallback(self):
        # Create files
        (self.project_dir / "test.py").write_text("def foo():\n    print('hello')\n    return True")
        (self.project_dir / "ignore.me").write_text("print('hello')")

        results = search_codebase(
            self.project_dir,
            "print",
            file_pattern="*.py",
            use_git_grep=False,
            context_lines=1
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['file'], "test.py")
        self.assertEqual(results[0]['line'], 2)
        self.assertEqual(results[0]['content'], "    print('hello')")
        self.assertEqual(results[0]['context_before'], ["def foo():"])
        self.assertEqual(results[0]['context_after'], ["    return True"])

    def test_search_regex(self):
        (self.project_dir / "test.txt").write_text("abc\n123\nxyz")

        results = search_codebase(
            self.project_dir,
            r"\d+",
            use_git_grep=False,
            is_regex=True
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['content'], "123")

if __name__ == '__main__':
    unittest.main()
