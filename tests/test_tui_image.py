import unittest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
import sys

# Mock PIL before importing tui_image if it's not installed, but here we assume it is or we mock it.
# We will rely on existing environment.

from shared.tui_image import ImageLabTab, generate_ascii_preview

class TestImageLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = ImageLabTab(self.project_dir)
        self.tab.manager = MagicMock()
        self.tab.notify = MagicMock()

        self.mock_widgets = {}
        def get_widget(selector, type=None):
            if selector not in self.mock_widgets:
                self.mock_widgets[selector] = MagicMock()
            return self.mock_widgets[selector]

        self.tab.query_one = MagicMock(side_effect=get_widget)

    def test_load_info(self):
        path = Path("test.png")
        self.tab.manager.get_info.return_value = {"format": "PNG", "width": 100}

        self.tab.load_info(path)

        self.tab.manager.get_info.assert_called_with(path)
        # Check table population
        table = self.tab.query_one("#img-info-table")
        table.clear.assert_called()
        table.add_row.assert_any_call("format", "PNG")

    async def test_run_convert(self):
        self.tab.selected_file = Path("test.png")
        self.tab.query_one("#img-conv-format").value = "JPEG"
        self.tab.query_one("#img-conv-output").value = "out.jpg"

        await self.tab.run_convert()

        expected_out = Path("test.png").parent / "out.jpg"
        self.tab.manager.convert.assert_called_with(Path("test.png"), expected_out, format="JPEG")
        self.tab.notify.assert_called()

    async def test_run_resize(self):
        self.tab.selected_file = Path("test.png")
        self.tab.query_one("#img-resize-w").value = "100"
        self.tab.query_one("#img-resize-h").value = "100"

        await self.tab.run_resize()

        # We don't check exact path as it's generated, but we verify resize is called
        self.tab.manager.resize.assert_called()
        args, kwargs = self.tab.manager.resize.call_args
        self.assertEqual(kwargs['width'], 100)
        self.assertEqual(kwargs['height'], 100)

    async def test_run_stego_hide(self):
        self.tab.selected_file = Path("test.png")
        self.tab.query_one("#img-stego-msg").value = "secret"
        self.tab.query_one("#img-stego-out").value = "secret.png"

        await self.tab.run_hide()

        expected_out = Path("test.png").parent / "secret.png"
        self.tab.manager.hide_message.assert_called_with(Path("test.png"), expected_out, "secret")

    @patch("shared.tui_image.Image")
    def test_generate_ascii_preview(self, mock_image):
        # Mock PIL Image
        mock_img_instance = MagicMock()
        mock_image.open.return_value = mock_img_instance
        mock_img_instance.width = 100
        mock_img_instance.height = 100
        mock_img_instance.resize.return_value = mock_img_instance
        mock_img_instance.convert.return_value = mock_img_instance
        # Mock getdata to return list of 0s (index 0 -> '@')
        mock_img_instance.getdata.return_value = [0] * (80 * 44)

        result = generate_ascii_preview(Path("test.png"), width=80)
        self.assertIsInstance(result, str)
        self.assertIn("@", result)

if __name__ == "__main__":
    unittest.main()
