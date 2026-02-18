import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from shared.tui_json import JsonLabTab


class TestJsonLabTab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = JsonLabTab(self.project_dir)
        # Mock internal components
        self.tab.manager = MagicMock()
        self.tab.notify = MagicMock()

        # Mock query_one
        self.mock_widgets = {}

        def get_widget(selector, type=None):
            if selector not in self.mock_widgets:
                self.mock_widgets[selector] = MagicMock()
            return self.mock_widgets[selector]

        self.tab.query_one = MagicMock(side_effect=get_widget)

    def test_load_file_success(self):
        # Setup
        path = Path("test.json")
        self.tab.manager.load_json.return_value = {"key": "value"}

        # Mock tree root
        mock_tree = self.tab.query_one("#json-tree")
        mock_tree.root = MagicMock()

        # Action
        self.tab.load_file(path)

        # Assert
        self.tab.manager.load_json.assert_called_with("test.json")
        self.assertEqual(self.tab.current_data, {"key": "value"})

        # Check UI updates
        self.tab.query_one("#lbl-json-structure").update.assert_called()
        self.assertEqual(self.tab.query_one("#btn-json-save").disabled, False)

    def test_on_update(self):
        # Setup
        self.tab.selected_path = ["key"]
        self.tab.current_data = {"key": "old"}

        # Mock input value
        mock_input = self.tab.query_one("#json-value-input")
        mock_input.value = '"new"'

        # Action
        self.tab.on_update()

        # Assert
        self.tab.manager.set.assert_called_with({"key": "old"}, ["key"], "new")

    def test_on_delete(self):
        # Setup
        self.tab.selected_path = ["key"]
        self.tab.current_data = {"key": "value"}

        # Action
        self.tab.on_delete()

        # Assert
        self.tab.manager.delete.assert_called_with({"key": "value"}, ["key"])
        self.assertIsNone(self.tab.selected_path)

    def test_on_save(self):
        # Setup
        self.tab.current_file = Path("test.json")
        self.tab.current_data = {"key": "value"}

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_dump:
                # Action
                self.tab.on_save()

                # Assert
                mock_file.assert_called_with(Path("test.json"), 'w', encoding='utf-8')
                mock_dump.assert_called_with({"key": "value"}, mock_file(), indent=2)


if __name__ == "__main__":
    unittest.main()
