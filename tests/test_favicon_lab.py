import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from shared.favicon_lab import FaviconManager
    HAS_FAVICON_DEPS = True
except ImportError:
    HAS_FAVICON_DEPS = False

try:
    import textual
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


@pytest.fixture
def mock_image():
    """Mock a Pillow Image object to prevent requiring real file I/O or PIL operations strictly during test isolation if needed."""
    pass

@pytest.mark.skipif(not HAS_FAVICON_DEPS, reason="Pillow is not installed")
def test_favicon_manager_initialization():
    manager = FaviconManager()
    assert manager is not None

@pytest.mark.skipif(not HAS_FAVICON_DEPS, reason="Pillow is not installed")
def test_get_html_tags():
    manager = FaviconManager()
    tags = manager.get_html_tags()
    assert "apple-touch-icon.png" in tags
    assert "favicon-32x32.png" in tags
    assert "favicon-16x16.png" in tags
    assert "site.webmanifest" in tags

@pytest.mark.skipif(not HAS_FAVICON_DEPS, reason="Pillow is not installed")
def test_generate_favicons(tmp_path):
    # Need a real tiny image to test actual PIL processing
    from PIL import Image
    manager = FaviconManager()

    input_img = tmp_path / "test_logo.png"
    out_dir = tmp_path / "public"

    # Create a dummy image
    img = Image.new('RGB', (512, 512), color = 'red')
    img.save(input_img)

    result = manager.generate(input_img, out_dir)

    assert result["success"] is True

    # Verify expected files exist
    assert (out_dir / "favicon.ico").exists()
    assert (out_dir / "apple-touch-icon.png").exists()
    assert (out_dir / "favicon-32x32.png").exists()
    assert (out_dir / "favicon-16x16.png").exists()
    assert (out_dir / "android-chrome-192x192.png").exists()
    assert (out_dir / "android-chrome-512x512.png").exists()
    assert (out_dir / "site.webmanifest").exists()

    # Verify site.webmanifest contents
    with open(out_dir / "site.webmanifest", "r") as f:
        data = json.load(f)
        assert data["name"] == "App"
        assert len(data["icons"]) == 2
        assert data["icons"][0]["sizes"] == "192x192"

@pytest.mark.skipif(not TEXTUAL_AVAILABLE or not HAS_FAVICON_DEPS, reason="Textual or Pillow not installed")
@pytest.mark.asyncio
async def test_tui_favicon_lab():
    from shared.tui_favicon import FaviconLabTab
    from textual.app import App

    class DummyApp(App):
        def compose(self):
            yield FaviconLabTab()

    app = DummyApp()
    async with app.run_test(headless=True) as pilot:
        assert pilot.app.query_one(FaviconLabTab) is not None
