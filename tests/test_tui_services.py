import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Button, RichLog, Input
from shared.tui_services import ServicesTab
from shared.process_manager import ServiceInfo

class ServicesTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield ServicesTab(self.project_dir)

class TestServicesTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = ServicesTestApp(self.project_dir)

    @patch("shared.tui_services.ServiceManager")
    async def test_add_service(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.list_services.return_value = []
        mock_instance.get_service.return_value = None

        mock_instance.add_service = MagicMock()

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ServicesTab)

            inp = tab.query_one("#services-new-cmd", Input)
            inp.value = "echo hello"

            # Manually trigger handler to avoid pilot flakiness with Inputs
            btn = tab.query_one("#btn-services-add", Button)
            await tab.on_button_pressed(Button.Pressed(btn))

            mock_instance.add_service.assert_called_with("echo", "echo hello")

    @patch("shared.tui_services.ServiceManager")
    async def test_start_service(self, MockManager):
        mock_instance = MockManager.return_value
        svc = ServiceInfo(name="test", command="test cmd", cwd=Path("."), status="Stopped")
        mock_instance.list_services.return_value = [svc]
        mock_instance.get_service.return_value = svc

        mock_instance.start_service = AsyncMock()
        mock_instance.stop_service = AsyncMock()
        mock_instance.restart_service = AsyncMock()

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ServicesTab)

            tab.selected_service = "test"
            tab.refresh_ui()
            await pilot.pause()

            btn_start = tab.query_one("#btn-services-start", Button)
            self.assertFalse(btn_start.disabled)

            # Click Start
            await pilot.click("#btn-services-start")
            await pilot.pause()

            mock_instance.start_service.assert_called_with("test")

if __name__ == "__main__":
    unittest.main()
