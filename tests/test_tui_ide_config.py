import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.widgets import Label, Checkbox, RichLog
from shared.tui_ide_config import IdeConfigTab

class TestIdeConfigTab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test")
        # Patch IdeConfigManager to avoid instantiation issues
        with patch('shared.tui_ide_config.IdeConfigManager') as MockManager:
            self.tab = IdeConfigTab(self.project_dir)
            self.mock_manager = MockManager.return_value

        # Setup mock return values
        self.mock_manager.detect_project_type.return_value = "python"
        self.mock_manager.get_config_previews.return_value = {
            "settings.json": {"a": 1},
            "launch.json": {"b": 2},
            "extensions.json": {"c": 3}
        }

        # Mock app property to avoid AttributeErrors if any widget logic accesses it
        self.tab._app = MagicMock()

    def test_refresh_preview(self):
        # Mock query_one to intercept widget lookups
        self.tab.query_one = MagicMock()

        self.tab.refresh_preview()

        self.mock_manager.detect_project_type.assert_called_once()
        self.mock_manager.get_config_previews.assert_called_once()

        # Verify calls to update UI
        # query_one should be called for:
        # 1. #val-ide-project-type (Label)
        # 2. #log-ide-settings (RichLog)
        # 3. #log-ide-launch (RichLog)
        # 4. #log-ide-extensions (RichLog)

        calls = self.tab.query_one.call_args_list
        selectors = [call.args[0] for call in calls]

        self.assertIn("#val-ide-project-type", selectors)
        self.assertIn("#log-ide-settings", selectors)
        self.assertIn("#log-ide-launch", selectors)
        self.assertIn("#log-ide-extensions", selectors)

    def test_generate_config(self):
        # Mock query_one
        checkbox_mock = MagicMock(spec=Checkbox)
        checkbox_mock.value = True

        log_mock = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if "chk-ide-force" in selector:
                return checkbox_mock
            if "log-ide-output" in selector:
                return log_mock
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_side_effect)
        self.tab.notify = MagicMock()

        self.mock_manager.generate_vscode_config.return_value = True

        self.tab.generate_config()

        self.mock_manager.generate_vscode_config.assert_called_with(force=True)
        self.tab.notify.assert_called_with("Configuration generated successfully.")

        # Verify log writing
        self.assertTrue(log_mock.write.called)

if __name__ == '__main__':
    unittest.main()
