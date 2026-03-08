import pytest
from textual.app import App, ComposeResult
from textual.widgets import Input, Select, RichLog, Button
from pathlib import Path
from unittest.mock import patch, MagicMock

from shared.tui_barcode import BarcodeLabTab

class BarcodeLabTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield BarcodeLabTab(self.project_dir)

@pytest.mark.asyncio
async def test_barcode_lab_tui_generate():
    project_dir = Path("/tmp/mock_project")
    app = BarcodeLabTestApp(project_dir)

    with patch("shared.tui_barcode.BarcodeLabManager") as MockManager:
        mock_manager_instance = MockManager.return_value
        mock_manager_instance.get_supported_formats.return_value = ["ean13", "code39"]
        mock_manager_instance.generate.return_value = (True, "Barcode saved.")

        async with app.run_test() as pilot:
            # We need to find the widgets and fill them
            await pilot.pause(0.1)

            data_input = app.query_one("#barcode-data-input", Input)
            data_input.value = "123456789012"

            type_select = app.query_one("#barcode-type-select", Select)
            type_select.value = "ean13"

            output_input = app.query_one("#barcode-output-input", Input)
            output_input.value = "test_barcode"

            # Click generate button
            await pilot.click("#btn-barcode-generate")
            await pilot.pause(0.1)

            mock_manager_instance.generate.assert_called_once_with("123456789012", "ean13", Path("test_barcode"))

            log = app.query_one("#barcode-log", RichLog)
            assert "Barcode saved." in "\n".join([line.text for line in log.lines])

@pytest.mark.asyncio
async def test_barcode_lab_tui_validate():
    project_dir = Path("/tmp/mock_project")
    app = BarcodeLabTestApp(project_dir)

    with patch("shared.tui_barcode.BarcodeLabManager") as MockManager:
        mock_manager_instance = MockManager.return_value
        mock_manager_instance.get_supported_formats.return_value = ["ean13", "code39"]
        mock_manager_instance.validate.return_value = (False, "Invalid data.")

        async with app.run_test() as pilot:
            await pilot.pause(0.1)

            data_input = app.query_one("#barcode-data-input", Input)
            data_input.value = "invalid_data"

            type_select = app.query_one("#barcode-type-select", Select)
            type_select.value = "ean13"

            # Click validate button
            await pilot.click("#btn-barcode-validate")
            await pilot.pause(0.1)

            mock_manager_instance.validate.assert_called_once_with("invalid_data", "ean13")

            log = app.query_one("#barcode-log", RichLog)
            assert "Invalid data." in "\n".join([line.text for line in log.lines])
