import pytest
from pathlib import Path

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    Image = None
    PILLOW_AVAILABLE = False

try:
    from textual.app import App
    from textual.widgets import Label, Input, Static, Button
    from shared.tui_favicon import FaviconLabTab
    TEXTUAL_AVAILABLE = True
except ImportError:
    App = object
    FaviconLabTab = object
    TEXTUAL_AVAILABLE = False


@pytest.fixture
def dummy_image(tmp_path):
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow is not installed")
    img_path = tmp_path / "test_logo.png"
    img = Image.new("RGBA", (512, 512), color="blue")
    img.save(str(img_path))
    return img_path


@pytest.mark.skipif(not TEXTUAL_AVAILABLE or not PILLOW_AVAILABLE, reason="Dependencies are not installed")
@pytest.mark.asyncio
async def test_tui_favicon_generate(tmp_path, dummy_image):
    class DummyApp(App):
        def compose(self):
            yield FaviconLabTab(project_dir=tmp_path)

    app = DummyApp()
    async with app.run_test(headless=True) as pilot:
        # Check title
        assert app.query_one("#favicon-title")

        # Verify initial states
        input_path = app.query_one("#favicon-input-path", Input)
        out_dir = app.query_one("#favicon-output-dir", Input)

        # Test empty generation
        await pilot.click("#favicon-generate-btn")
        result = str(app.query_one("#favicon-generate-result", Static).render())
        assert "Input path is required" in result

        # Set inputs for generation
        input_path.value = str(dummy_image)
        out_dir.value = str(tmp_path / "out")

        await pilot.pause()

        # Test clicking directly using the app method instead of pilot.click
        btn = app.query_one("#favicon-generate-btn", Button)
        btn.press()
        await pilot.pause()
        result = str(app.query_one("#favicon-generate-result", Static).render())

        assert "Successfully" in result

        # Check files were created
        expected = tmp_path / "out" / "favicon.ico"
        assert expected.exists()


@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual is not installed")
@pytest.mark.asyncio
async def test_tui_favicon_pillow_missing(tmp_path, monkeypatch):
    class MockFaviconManager:
        def __init__(self):
            self.pillow_available = False

    monkeypatch.setattr("shared.tui_favicon.FaviconManager", MockFaviconManager)

    class DummyApp(App):
        def compose(self):
            yield FaviconLabTab(project_dir=tmp_path)

    app = DummyApp()
    async with app.run_test(headless=True) as pilot:
        # TUI should yield a warning label instead of regular UI
        warning = app.query_one("#favicon-warning", Label)
        assert "Pillow is required" in str(warning.render())
