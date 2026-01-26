import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Button, DataTable
from shared.tui_docker import DockerTab

class DockerTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield DockerTab(self.project_dir)

class TestDockerTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = DockerTestApp(self.project_dir)

    @patch("shared.tui_docker.DockerManager")
    async def test_refresh_ui(self, MockManager):
        mock_instance = MockManager.return_value
        # Mock list_containers to return a valid list
        mock_instance.list_containers.return_value = [
            {"ID": "1234567890ab", "Image": "test-img", "Status": "Up 2 hours", "Names": "test-container"}
        ]

        async with self.app.run_test() as pilot:
            # Wait for mount and initial refresh
            await pilot.pause(0.5)

            tab = self.app.query_one(DockerTab)
            table = tab.query_one("#docker-table", DataTable)

            # Check if table populated (row keys are short IDs)
            self.assertIn("1234567890ab", table.rows)

            # Select row manually to simulate user interaction
            tab.selected_container = "1234567890ab"
            tab._update_buttons({"Status": "Up 2 hours", "ID": "1234567890ab"})

            await pilot.pause()

            # Check Start button (should be disabled for running container)
            btn_start = tab.query_one("#btn-docker-start", Button)
            self.assertTrue(btn_start.disabled)

            # Check Stop button (should be enabled)
            btn_stop = tab.query_one("#btn-docker-stop", Button)
            self.assertFalse(btn_stop.disabled)

    @patch("shared.tui_docker.DockerManager")
    async def test_actions(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.list_containers.return_value = [
            {"ID": "123", "Image": "test", "Status": "Up", "Names": "test"}
        ]
        mock_instance.stop_container = MagicMock()

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(DockerTab)

            # Select container
            tab.selected_container = "123"
            tab._update_buttons({"Status": "Up", "ID": "123"})

            # Click Stop
            await pilot.click("#btn-docker-stop")
            await pilot.pause(0.2)

            # Verify stop called.
            # TUI calls start_container in a thread, so we waited with pause(0.2).
            # We verify the mock was called.
            mock_instance.stop_container.assert_called_with("123")

if __name__ == "__main__":
    unittest.main()
