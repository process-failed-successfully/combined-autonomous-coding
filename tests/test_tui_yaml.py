import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from shared.tui_yaml import YamlLabTab
import yaml

class TestYamlLabTab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = YamlLabTab(self.project_dir)
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
        path = Path("test.yaml")
        # Manager load_yaml returns python obj
        self.tab.manager.load_yaml.return_value = {"key": "value"}

        # Mock tree root
        mock_tree = self.tab.query_one("#yaml-tree")
        mock_tree.root = MagicMock()

        # Action
        self.tab.load_file(path)

        # Assert
        self.tab.manager.load_yaml.assert_called_with("test.yaml")
        self.assertEqual(self.tab.current_data, {"key": "value"})

        # Check UI updates
        self.tab.query_one("#lbl-yaml-structure").update.assert_called()
        self.assertEqual(self.tab.query_one("#btn-yaml-save").disabled, False)

    def test_on_update(self):
        # Setup
        self.tab.selected_path = ["key"]
        self.tab.current_data = {"key": "old"}

        # Mock input value
        mock_input = self.tab.query_one("#yaml-value-input")
        # In TUI logic we use yaml.safe_load(val_str)
        # So providing '"new"' (JSON string) works as YAML
        mock_input.value = '"new"'

        # Action
        self.tab.on_update()

        # Assert
        self.tab.manager.set.assert_called_with({"key": "old"}, ["key"], "new")

    def test_on_update_invalid_yaml(self):
         # Setup
        self.tab.selected_path = ["key"]
        self.tab.current_data = {"key": "old"}

        # Mock input value with invalid yaml
        mock_input = self.tab.query_one("#yaml-value-input")
        mock_input.value = ': invalid'

        # Action
        self.tab.on_update()

        # Assert
        self.tab.manager.set.assert_not_called()
        # Verify log message about error
        self.tab.query_one("#yaml-log").write.assert_called()

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
        self.tab.current_file = Path("test.yaml")
        self.tab.current_data = {"key": "value"}
        # Mock dump_yaml to return string
        self.tab.manager.dump_yaml.return_value = "key: value\n"

        with patch("builtins.open", mock_open()) as mock_file:
            # Action
            self.tab.on_save()

            # Assert
            self.tab.manager.dump_yaml.assert_called_with({"key": "value"})
            mock_file.assert_called_with(Path("test.yaml"), 'w', encoding='utf-8')
            mock_file().write.assert_called_with("key: value\n")


if __name__ == "__main__":
    unittest.main()
