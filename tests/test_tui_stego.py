import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
from shared.tui_stego import StegoLabTab
from shared.stego_lab import HAS_PILLOW

# Create a dummy app to host the tab
class DummyStegoApp(App[None]):
    def compose(self) -> ComposeResult:
        yield StegoLabTab()

@pytest.fixture
def temp_images():
    if not HAS_PILLOW:
        pytest.skip("Pillow not installed.")
        return

    from PIL import Image
    with tempfile.TemporaryDirectory() as temp_dir:
        input_img = os.path.join(temp_dir, "test_input.png")
        output_img = os.path.join(temp_dir, "test_output.png")
        img = Image.new('RGB', (100, 100), color='white')
        img.save(input_img)
        yield input_img, output_img

@pytest.mark.asyncio
async def test_stego_tab_hide_text(temp_images):
    if not HAS_PILLOW:
        return

    input_img, output_img = temp_images
    app = DummyStegoApp()

    async with app.run_test() as pilot:
        tab = app.query_one(StegoLabTab)

        # Set up mock notifications
        tab.notify = MagicMock()

        # Fill inputs
        input_img_widget = tab.query_one("#stego-hide-img")
        input_out_widget = tab.query_one("#stego-hide-out")
        input_text_widget = tab.query_one("#stego-input-text")

        input_img_widget.value = input_img
        input_out_widget.value = output_img
        input_text_widget.text = "Hello Hidden World!"

        # Click Hide
        btn = tab.query_one("#btn-stego-hide")
        btn.press()
        await pilot.pause(0.1)

        # Check notification
        tab.notify.assert_called_with(f"Text successfully hidden in '{output_img}'.", severity="information")

        # Verify output exists
        assert os.path.exists(output_img)

@pytest.mark.asyncio
async def test_stego_tab_extract_text(temp_images):
    if not HAS_PILLOW:
        return

    input_img, output_img = temp_images

    # Hide text first
    from shared.stego_lab import StegoManager
    manager = StegoManager()
    manager.hide_text(input_img, "Secret Message", output_img)

    app = DummyStegoApp()

    async with app.run_test() as pilot:
        tab = app.query_one(StegoLabTab)

        # Set up mock notifications
        tab.notify = MagicMock()

        # Fill input for extraction
        extract_img_widget = tab.query_one("#stego-extract-img")
        extract_img_widget.value = output_img

        # Click Extract
        btn = tab.query_one("#btn-stego-extract")
        btn.press()
        await pilot.pause(0.1)

        # Check notification
        tab.notify.assert_called_with("Text extracted successfully.", severity="information")

        # Check text in output area
        output_text_widget = tab.query_one("#stego-output-text")
        assert output_text_widget.text == "Secret Message"
