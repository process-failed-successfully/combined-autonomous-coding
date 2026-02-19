import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Patch sys.modules to prevent actual textual imports if they cause issues,
# but we need some base classes.
# Assuming environment has textual installed, so we import normally.
from shared.tui_markdown import MarkdownLabTab

class TestMarkdownLabTab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = MarkdownLabTab(self.project_dir)

        # Mock Manager
        self.tab.manager = MagicMock()

        # Mock query_one results
        self.mock_editor = MagicMock()
        self.mock_editor.text = ""

        self.mock_preview = MagicMock()

        self.mock_log = MagicMock()

        self.mock_btn_save = MagicMock()
        self.mock_btn_preview = MagicMock()
        self.mock_btn_toc = MagicMock()
        self.mock_btn_table = MagicMock()
        self.mock_btn_stats = MagicMock()
        self.mock_btn_lint = MagicMock()

        def query_one_side_effect(selector, type=None):
            if selector == "#md-editor": return self.mock_editor
            if selector == "#md-preview": return self.mock_preview
            if selector == "#md-tool-output": return self.mock_log
            if selector == "#btn-md-save": return self.mock_btn_save
            if selector == "#btn-md-preview": return self.mock_btn_preview
            if selector == "#btn-md-toc": return self.mock_btn_toc
            if selector == "#btn-md-table": return self.mock_btn_table
            if selector == "#btn-md-stats": return self.mock_btn_stats
            if selector == "#btn-md-lint": return self.mock_btn_lint
            raise ValueError(f"Unexpected selector: {selector}")

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Mock notify
        self.tab.notify = MagicMock()

    def test_load_file_success(self):
        file_path = MagicMock(spec=Path)
        file_path.name = "test.md"
        file_path.read_text.return_value = "# Hello"
        file_path.suffix = ".md" # Mock suffix for directory tree event check if needed

        self.tab.load_file(file_path)

        self.assertEqual(self.tab.current_file, file_path)
        self.assertEqual(self.mock_editor.text, "# Hello")
        self.mock_preview.update.assert_called_with("# Hello")

        # check enabled
        self.assertEqual(self.mock_btn_save.disabled, False)
        self.assertEqual(self.mock_btn_toc.disabled, False)

    def test_load_file_failure(self):
        file_path = MagicMock(spec=Path)
        file_path.name = "test.md"
        file_path.read_text.side_effect = Exception("Read Error")

        self.tab.load_file(file_path)

        self.mock_log.write.assert_called()
        # check disabled
        self.assertEqual(self.mock_btn_save.disabled, True)

    def test_save_file(self):
        self.tab.current_file = MagicMock(spec=Path)
        self.tab.current_file.name = "test.md"
        self.mock_editor.text = "New Content"

        self.tab.on_save()

        self.tab.current_file.write_text.assert_called_with("New Content", encoding="utf-8")
        self.mock_log.write.assert_called()

    def test_preview_click(self):
        self.mock_editor.text = "Preview Me"
        self.tab.on_preview_click()
        self.mock_preview.update.assert_called_with("Preview Me")

    def test_toc_generation(self):
        self.mock_editor.text = "# H1"
        self.tab.manager.generate_toc.return_value = "- [H1](#h1)"
        self.tab.manager.insert_toc.return_value = "TOC\n# H1"

        self.tab.on_toc()

        self.tab.manager.generate_toc.assert_called_with("# H1")
        self.tab.manager.insert_toc.assert_called_with("# H1", "- [H1](#h1)")
        self.assertEqual(self.mock_editor.text, "TOC\n# H1")
        self.mock_preview.update.assert_called()

    def test_format_table(self):
        self.mock_editor.text = "|a|b|"
        self.tab.manager.format_table.return_value = "| a | b |"

        self.tab.on_table()

        self.assertEqual(self.mock_editor.text, "| a | b |")
        self.mock_preview.update.assert_called()

    def test_stats(self):
        self.mock_editor.text = "content"
        self.tab.manager.get_stats.return_value = {"words": 1}

        self.tab.on_stats()

        self.tab.manager.get_stats.assert_called_with("content")
        self.mock_log.write.assert_called()

    def test_lint(self):
        self.tab.current_file = MagicMock(spec=Path)
        self.tab.current_file.parent = Path("/tmp")
        self.mock_editor.text = "content"
        self.tab.manager.lint.return_value = [{"line": 1, "type": "error", "message": "msg"}]

        self.tab.on_lint()

        self.tab.manager.lint.assert_called_with("content", root_dir=Path("/tmp"))
        self.mock_log.write.assert_called()

if __name__ == '__main__':
    unittest.main()
