import unittest
from unittest.mock import patch, MagicMock
from textual.app import App, ComposeResult
from pathlib import Path
from shared.tui_static import StaticLabTab

class StaticLabTestApp(App):
    def __init__(self, project_dir=None):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield StaticLabTab(project_dir=self.project_dir)

class TestStaticLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/dummy")

    async def test_static_tab_mount(self):
        """Test that the static tab mounts correctly."""
        app = StaticLabTestApp(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            tab = app.query_one(StaticLabTab)
            self.assertIsNotNone(tab)

            # Check that initial values are set
            dir_input = app.query_one("#static-dir")
            self.assertEqual(dir_input.value, str(self.project_dir))

            port_input = app.query_one("#static-port")
            self.assertEqual(port_input.value, "8000")

    @patch("shared.tui_static.StaticLabManager")
    async def test_start_and_stop_server(self, mock_manager_class):
        """Test starting and stopping the server via UI buttons."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        app = StaticLabTestApp(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            tab = app.query_one(StaticLabTab)

            # Click Start
            start_btn = app.query_one("#btn-static-start")
            pilot.app.query_one("#btn-static-start").press()
            await pilot.pause()
            await pilot.pause()

            # Ensure Manager was created with correct args
            mock_manager_class.assert_called_once()
            config = mock_manager_class.call_args[0][0]
            self.assertEqual(config["port"], 8000)
            self.assertEqual(config["directory"], str(self.project_dir))

            # Verify UI state changed
            self.assertTrue(tab.server_running)
            self.assertTrue(start_btn.disabled)
            stop_btn = app.query_one("#btn-static-stop")
            self.assertFalse(stop_btn.disabled)

            # Click Stop
            pilot.app.query_one("#btn-static-stop").press()
            await pilot.pause()
            await pilot.pause()

            # Verify manager.stop was called
            mock_manager.stop.assert_called_once()

            # Verify UI state restored
            self.assertFalse(tab.server_running)
            self.assertFalse(start_btn.disabled)
            self.assertTrue(stop_btn.disabled)

if __name__ == "__main__":
    unittest.main()
