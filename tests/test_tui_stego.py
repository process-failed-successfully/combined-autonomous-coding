import pytest
from textual.app import App
from unittest.mock import MagicMock, patch

from shared.tui_stego import StegoLabTab


class DummyApp(App):
    """Dummy Textual app to run the StegoLabTab."""
    def compose(self):
        yield StegoLabTab()


@pytest.mark.asyncio
async def test_stego_tui_missing_pillow():
    """Test StegoLabTab when Pillow is missing."""
    with patch('shared.tui_stego.StegoManager', side_effect=ImportError):
        app = DummyApp()
        async with app.run_test():
            # Find the error label explicitly, the first label is just the title
            labels = app.query("StegoLabTab Label")
            found_error = False
            for label in labels:
                rendered_text = str(label.render())
                if "Error" in rendered_text or "Pillow" in rendered_text:
                    found_error = True
                    break
            assert found_error


@pytest.mark.asyncio
async def test_stego_tui_hide_success():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Access the tab
        tab = app.query_one(StegoLabTab)

        if tab.manager is None:
            pytest.skip("Pillow not installed, cannot test hide/extract")

        # Mock the manager methods
        tab.manager.hide = MagicMock(return_value=True)

        # Set values
        app.query_one("#stego-hide-image").value = "test.png"
        app.query_one("#stego-hide-message").value = "Secret"
        app.query_one("#stego-hide-output").value = "out.png"

        # Bypass OutOfBounds error by triggering the button press handler directly
        await tab.on_button_pressed(MagicMock(button=MagicMock(id="btn-stego-hide")))
        await pilot.pause(0.1)

        # Assert manager called
        tab.manager.hide.assert_called_once_with("test.png", "Secret", "out.png")

        # Assert label updated
        result_label = app.query_one("#stego-hide-result")
        assert "Message hidden successfully" in str(result_label.render())


@pytest.mark.asyncio
async def test_stego_tui_extract_success():
    app = DummyApp()
    async with app.run_test() as pilot:
        tab = app.query_one(StegoLabTab)

        if tab.manager is None:
            pytest.skip("Pillow not installed, cannot test hide/extract")

        tab.manager.extract = MagicMock(return_value="Extracted Secret")

        app.query_one("#stego-extract-image").value = "out.png"

        # Bypass OutOfBounds error by triggering the button press handler directly
        await tab.on_button_pressed(MagicMock(button=MagicMock(id="btn-stego-extract")))
        await pilot.pause(0.1)

        tab.manager.extract.assert_called_once_with("out.png")

        result_label = app.query_one("#stego-extract-result")
        assert "Extracted Secret" in str(result_label.render())
