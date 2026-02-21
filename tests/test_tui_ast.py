import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile
from textual.widgets import TextArea, Tree, RichLog
from textual.app import App, ComposeResult

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui_ast import ASTExplorerTab

class ASTTestApp(App):
    """Minimal app for testing the tab."""
    def compose(self) -> ComposeResult:
        yield ASTExplorerTab()

class TestTUIAST(unittest.IsolatedAsyncioTestCase):
    async def test_ast_explorer_structure(self):
        """Test that the AST Explorer tab has the correct widgets."""
        app = ASTTestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(ASTExplorerTab)
            self.assertIsNotNone(tab)

            # Check widgets
            self.assertIsInstance(tab.query_one("#code-input"), TextArea)
            self.assertIsInstance(tab.query_one("#ast-tree"), Tree)
            self.assertIsInstance(tab.query_one("#node-details"), RichLog)

    @patch("shared.tui_ast.ASTLabManager")
    async def test_code_update_triggers_parse(self, MockManager):
        """Test that changing code triggers AST parsing and tree update."""
        mock_manager = MockManager.return_value
        # Mock parse_code to return a simple AST
        import ast
        mock_manager.parse_code.return_value = ast.parse("x=1")

        app = ASTTestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(ASTExplorerTab)

            # Simulate typing code
            code_input = tab.query_one("#code-input", TextArea)
            code_input.text = "x=1"

            # Allow events to process
            await pilot.pause()

            # Verify parse_code called
            mock_manager.parse_code.assert_called_with("x=1")

            # Verify tree populated (root + Module + Assign)
            tree = tab.query_one("#ast-tree", Tree)
            # Tree structure: Root -> Module -> Assign
            # Because Textual Tree is dynamic, checking children count is tricky if async,
            # but here it is synchronous update.
            # Root is "Root", then it gets updated to "Module".
            self.assertEqual(str(tree.root.label), "Module")
            self.assertTrue(len(tree.root.children) > 0)

if __name__ == "__main__":
    unittest.main()
