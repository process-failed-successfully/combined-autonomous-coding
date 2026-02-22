import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from shared.tui_gitignore import GitignoreLabTab
from textual.widgets import ListView, TextArea, Input, Button

class TestGitignoreLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/mock_project")
        self.tab = GitignoreLabTab(self.project_dir)
        # Mock the manager
        self.tab.manager = MagicMock()
        self.tab.notify = MagicMock()

    async def test_mount_and_load_templates(self):
        # Setup mock manager return values
        self.tab.manager.list_templates.return_value = ["python", "node"]

        # Mock UI elements
        mock_list = MagicMock(spec=ListView)
        mock_list.clear = MagicMock()
        mock_list.append = MagicMock()

        def query_one_side_effect(selector, type=None):
            if selector == "#gitignore-template-list":
                return mock_list
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Call load_templates directly (simulating on_mount)
        self.tab.load_templates()

        mock_list.clear.assert_called_once()
        self.assertEqual(mock_list.append.call_count, 2)

    async def test_template_selection(self):
        self.tab.manager.get_template.return_value = "*.pyc"

        mock_preview = MagicMock(spec=TextArea)
        mock_btn_append = MagicMock()
        mock_btn_overwrite = MagicMock()

        def query_one_side_effect(selector, type=None):
            if selector == "#gitignore-preview":
                return mock_preview
            if selector == "#btn-gitignore-append":
                return mock_btn_append
            if selector == "#btn-gitignore-overwrite":
                return mock_btn_overwrite
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Create a mock event
        event = MagicMock()
        item = MagicMock()
        item.name = "python"
        event.item = item

        # Simulate selection
        self.tab.on_template_selected(event)

        self.assertEqual(self.tab.selected_template, "python")
        self.tab.manager.get_template.assert_called_with("python")
        self.assertEqual(mock_preview.text, "*.pyc")
        self.assertEqual(mock_btn_append.disabled, False)
        self.assertEqual(mock_btn_overwrite.disabled, False)

    async def test_append_action(self):
        self.tab.selected_template = "python"
        self.tab.manager.append.return_value = True

        # on_append is synchronous
        self.tab.on_append()

        self.tab.manager.append.assert_called_with(["python"])
        self.tab.notify.assert_called_with("Appended 'python' to .gitignore.")

    async def test_overwrite_action_with_confirmation(self):
        self.tab.selected_template = "python"

        # Mock Button
        mock_btn = MagicMock(spec=Button)
        mock_btn.label = "Overwrite .gitignore"
        mock_btn.variant = "warning"

        def query_one_side_effect(selector, type=None):
            if selector == "#btn-gitignore-overwrite":
                return mock_btn
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Mock Timer
        self.tab.set_timer = MagicMock()

        # Mock Manager
        self.tab.manager.generate.return_value = "*.pyc"

        # --- First Click (Confirmation Request) ---
        self.tab.on_overwrite()

        self.assertEqual(str(mock_btn.label), "Confirm Overwrite?")
        self.assertEqual(mock_btn.variant, "error")
        self.tab.set_timer.assert_called_once()
        self.tab.manager.generate.assert_not_called() # Should not overwrite yet

        # --- Second Click (Confirmed) ---
        # Mock file writing
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            self.tab.on_overwrite()

            self.tab.manager.generate.assert_called_with(["python"])
            mock_file.assert_called()
            mock_file().write.assert_called()
            self.tab.notify.assert_called_with("Overwritten .gitignore with 'python'.")

            # Check reset
            self.assertEqual(str(mock_btn.label), "Overwrite .gitignore")
            self.assertEqual(mock_btn.variant, "warning")

    async def test_check_ignore_action(self):
        # Mock Input
        mock_input = MagicMock(spec=Input)
        mock_input.value = "test.pyc"

        mock_output = MagicMock(spec=TextArea)

        def query_one_side_effect(selector, type=None):
            if selector == "#gitignore-check-input":
                return mock_input
            if selector == "#gitignore-check-output":
                return mock_output
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Need to patch asyncio.to_thread because it's used in the handler
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = {
                "message": "Ignored",
                "details": ".gitignore:1:*.pyc"
            }

            await self.tab.on_check()

            mock_to_thread.assert_called_once()
            self.assertEqual(mock_output.text, "Ignored\n\n.gitignore:1:*.pyc")

if __name__ == "__main__":
    unittest.main()
