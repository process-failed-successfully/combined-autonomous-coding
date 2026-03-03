import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.tui_pack import PackLabTab

class TestPackLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # We need to test the logic manually due to textual ContextVars limitations when instantiated standalone
        pass

    @patch("shared.tui_pack.PackManager")
    async def test_pack_tab_loads(self, mock_pack_manager):
        project_dir = Path("/tmp/mock/project")

        tab = PackLabTab(project_dir=project_dir)
        self.assertIsNotNone(tab)
        self.assertEqual(tab.project_dir, project_dir)

    @patch("shared.tui_pack.PackManager")
    @patch("shared.tui_pack.PackLabTab.app", new_callable=unittest.mock.PropertyMock)
    async def test_pack_interaction(self, mock_app_property, mock_pack_manager):
        project_dir = Path("/tmp/mock/project")

        tab = PackLabTab(project_dir=project_dir)
        mock_app = MagicMock()
        mock_app_property.return_value = mock_app

        # We mock query_one
        mock_input_include = MagicMock()
        mock_input_include.value = "*.py"

        mock_input_exclude = MagicMock()
        mock_input_exclude.value = "*.md"

        mock_select_format = MagicMock()
        mock_select_format.value = "xml"

        mock_textarea = MagicMock()

        def mock_query_one(query, cls=None):
            if query == "#input-include":
                return mock_input_include
            elif query == "#input-exclude":
                return mock_input_exclude
            elif query == "#select-format":
                return mock_select_format
            elif query == "#text-preview":
                return mock_textarea
            return MagicMock()

        tab.query_one = mock_query_one

        # Mock manager
        tab.manager.get_files.return_value = [Path("test1.py"), Path("test2.py")]
        tab.manager.pack.return_value = "### Mock XML Output"

        # Test pack press
        tab.on_pack_pressed()

        tab.manager.get_files.assert_called_once_with(include_patterns=["*.py"], exclude_patterns=["*.md"])
        tab.manager.pack.assert_called_once_with([Path("test1.py"), Path("test2.py")], format="xml")
        self.assertEqual(mock_textarea.text, "### Mock XML Output")
        mock_app.notify.assert_called_with("Successfully packed 2 files.", severity="information")

        # Test copy
        mock_textarea.text = "### Mock XML Output"
        tab.on_copy_pressed()
        mock_app.copy_to_clipboard.assert_called_once_with("### Mock XML Output")
        mock_app.notify.assert_called_with("Packed content copied to clipboard!", severity="information")

        # Test copy empty
        mock_textarea.text = ""
        mock_app.copy_to_clipboard.reset_mock()
        tab.on_copy_pressed()
        mock_app.copy_to_clipboard.assert_not_called()
        mock_app.notify.assert_called_with("Nothing to copy.", severity="warning")

        # Test clear
        tab.on_clear_pressed()
        self.assertEqual(mock_textarea.text, "")
        mock_app.notify.assert_called_with("Preview cleared.", severity="information")
