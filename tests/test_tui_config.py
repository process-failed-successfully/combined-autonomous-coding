import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import sys
import shutil
import tempfile
import yaml

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Input, Select, Checkbox
from shared.tui import ConfigTab

class TestConfigTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()
        self.config_path = self.project_dir / "agent_config.yaml"

        # Mock load_config_from_file
        self.patcher_load = patch("shared.tui.load_config_from_file")
        self.mock_load = self.patcher_load.start()

        # Default mock config
        self.mock_config = {
            "agent_type": "gemini",
            "model": "gemini-1.5-flash",
            "max_iterations": 10,
            "manager_frequency": 5,
            "slack_webhook_url": "https://slack.example.com",
            "notification_settings": {
                "iteration": True,
                "manager": False
            },
            "jira": {
                "url": "https://jira.example.com"
            }
        }
        self.mock_load.return_value = self.mock_config

    def tearDown(self):
        self.patcher_load.stop()
        shutil.rmtree(self.test_dir)

    async def test_load_config_ui(self):
        """Test that configuration is loaded into widgets."""
        tab = ConfigTab(self.project_dir)

        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # Verify values
            self.assertEqual(app.query_one("#cfg-agent-type", Select).value, "gemini")
            self.assertEqual(app.query_one("#cfg-model", Input).value, "gemini-1.5-flash")
            self.assertEqual(app.query_one("#cfg-max-iterations", Input).value, "10")
            self.assertEqual(app.query_one("#cfg-slack", Input).value, "https://slack.example.com")
            self.assertEqual(app.query_one("#cfg-notify-iteration", Checkbox).value, True)
            self.assertEqual(app.query_one("#cfg-notify-manager", Checkbox).value, False)
            self.assertEqual(app.query_one("#cfg-jira-url", Input).value, "https://jira.example.com")

    async def test_save_config_ui(self):
        """Test that configuration is saved."""
        tab = ConfigTab(self.project_dir)

        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # Modify values
            app.query_one("#cfg-model", Input).value = "gpt-4o"
            app.query_one("#cfg-max-iterations", Input).value = "99"
            app.query_one("#cfg-notify-error", Checkbox).value = True

            # Mock file writing
            # We must patch builtins.open where it is used. ConfigTab uses 'open' directly.
            # However, since ConfigTab is in shared.tui, and we imported it, patching builtins.open
            # in the test scope usually works if ConfigTab calls open().
            with patch("builtins.open", mock_open()) as m_open:
                # Click save
                app.query_one("#btn-cfg-save").press()
        await pilot.pause()

                # Check if file was opened for writing
                m_open.assert_called_with(self.config_path, "w")

                # Check written content
                handle = m_open()
                # Get all write calls
                written_content = "".join(call.args[0] for call in handle.write.call_args_list)

                # Parse written yaml
                saved_config = yaml.safe_load(written_content)

                self.assertEqual(saved_config["model"], "gpt-4o")
                self.assertEqual(saved_config["max_iterations"], 99)
                self.assertTrue(saved_config["notification_settings"]["error"])

if __name__ == "__main__":
    unittest.main()
