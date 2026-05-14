import pytest

try:
    import textual
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


if TEXTUAL_AVAILABLE and PILLOW_AVAILABLE:
    from textual.app import App
    from shared.tui_favicon import FaviconLabTab

    class DummyFaviconApp(App):
        def compose(self):
            yield FaviconLabTab()
else:
    DummyFaviconApp = object


@pytest.mark.asyncio
@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual is required")
@pytest.mark.skipif(not PILLOW_AVAILABLE, reason="Pillow is required")
async def test_tui_favicon_rendering(tmp_path):
    # Just render the app to ensure no crashes
    app = DummyFaviconApp()
    async with app.run_test(headless=True) as pilot:
        assert app.query_one("FaviconLabTab") is not None

        # Click the generate button without providing input
        button = app.query_one("#btn-favicon-generate")
        button.press()
        await pilot.pause()

        # Status should show error about missing input
        status_text = str(app.query_one("#favicon-status").render())
        assert "Please specify an input image" in status_text
