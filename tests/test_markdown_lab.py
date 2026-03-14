import unittest
from unittest.mock import patch
from shared.markdown_lab import MarkdownLabManager


class TestMarkdownLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MarkdownLabManager()

    def test_generate_toc(self):
        text = """
# Header 1
Some text.
## Header 2
More text.
### Header 3
Even more text.
## Header 2-2
        """
        expected_toc = """- [Header 1](#header-1)
  - [Header 2](#header-2)
    - [Header 3](#header-3)
  - [Header 2-2](#header-2-2)"""

        self.assertEqual(self.manager.generate_toc(text), expected_toc)

    def test_generate_toc_depth(self):
        text = """
# Header 1
## Header 2
### Header 3
        """
        expected_toc = """- [Header 1](#header-1)
  - [Header 2](#header-2)"""

        self.assertEqual(self.manager.generate_toc(text, depth=2), expected_toc)

    def test_insert_toc(self):
        text = """# Title
Some content.
<!-- TOC -->
More content."""
        toc = "- [Title](#title)"
        expected = """# Title
Some content.
<!-- TOC -->

- [Title](#title)
More content."""
        self.assertEqual(self.manager.insert_toc(text, toc), expected)

    def test_insert_toc_prepend(self):
        text = """# Title
Some content."""
        toc = "- [Title](#title)"
        # Note: logic adds newlines around TOC block
        expected = """# Title

## Table of Contents

- [Title](#title)

Some content."""
        self.assertEqual(self.manager.insert_toc(text, toc), expected)

    def test_get_stats(self):
        text = """
# Title
Word count check.
[Link](http://example.com)
![Image](img.png)
```python
print("code")
```
        """
        stats = self.manager.get_stats(text)
        # Assuming simple split() on words.
        # #, Title, Word, count, check., [Link](http://example.com), ![Image](img.png), ```python, print("code"), ```
        # That is 10 items.
        self.assertEqual(stats['words'], 10)

        self.assertEqual(stats['headers'], 1)
        self.assertEqual(stats['links'], 1)
        self.assertEqual(stats['images'], 1)
        self.assertEqual(stats['code_blocks'], 1)

    def test_format_table(self):
        text = """
| Col1 | Col2 |
|---|---|
| Val1 | Val2 |
| Longer Val | V |
"""
        formatted = self.manager.format_table(text)
        # Note: my implementation adds newline at start if present in input logic
        self.assertIn("| Col1       | Col2 |", formatted)
        self.assertIn("| ---------- | ---- |", formatted)
        self.assertIn("| Val1       | Val2 |", formatted)
        self.assertIn("| Longer Val | V    |", formatted)

    def test_lint_header_hierarchy(self):
        text = """
# H1
### H3 (Skip H2)
"""
        issues = self.manager.lint(text)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['type'], 'header-hierarchy')

    def test_lint_missing_alt(self):
        text = """
![](img.png)
"""
        issues = self.manager.lint(text)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['type'], 'missing-alt-text')

    @patch('sys.exit')
    @patch('shared.tui.AgentTUI')
    def test_markdown_lab_tui_launch(self, mock_agent_tui, mock_exit):
        import sys
        from main import parse_args, run_markdown_lab

        test_args = ["main.py", "markdown-lab", "tui"]
        with patch.object(sys, 'argv', test_args):
            args = parse_args()

            mock_exit.side_effect = SystemExit(0)
            with self.assertRaises(SystemExit) as cm:
                run_markdown_lab(args)

            self.assertEqual(cm.exception.code, 0)
            mock_agent_tui.assert_called_once()
            mock_app = mock_agent_tui.return_value
            mock_app.run.assert_called_once()


if __name__ == '__main__':
    unittest.main()
