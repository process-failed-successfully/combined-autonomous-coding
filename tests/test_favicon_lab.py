import os
import pytest
from pathlib import Path
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    from shared.favicon_lab import FaviconManager
    FAVICON_AVAILABLE = True
except ImportError:
    FAVICON_AVAILABLE = False


@pytest.fixture
def temp_image_path(tmp_path):
    if not PILLOW_AVAILABLE:
        pytest.skip("Pillow not available")

    img_path = tmp_path / "test_logo.png"
    # Create a small red image
    img = Image.new('RGB', (100, 100), color='red')
    with open(str(img_path), 'wb') as f:
        img.save(f, format='PNG')
    return str(img_path)


@pytest.mark.skipif(not PILLOW_AVAILABLE or not FAVICON_AVAILABLE, reason="Pillow or FaviconManager not available")
def test_favicon_manager_generate(temp_image_path, tmp_path):
    manager = FaviconManager()
    output_dir = tmp_path / "out"

    # Generate favicons
    result = manager.generate(temp_image_path, str(output_dir))

    assert result is True

    # Check that output files were created
    expected_files = [
        "apple-touch-icon.png",
        "android-chrome-192x192.png",
        "android-chrome-512x512.png",
        "favicon-32x32.png",
        "favicon-16x16.png",
        "favicon.ico",
        "site.webmanifest"
    ]

    for filename in expected_files:
        assert (output_dir / filename).exists(), f"Missing {filename}"


@pytest.mark.skipif(not PILLOW_AVAILABLE or not FAVICON_AVAILABLE, reason="Pillow or FaviconManager not available")
def test_favicon_manager_generate_missing_file(tmp_path):
    manager = FaviconManager()
    result = manager.generate(str(tmp_path / "does_not_exist.png"), str(tmp_path))
    assert result is False


@pytest.mark.skipif(not PILLOW_AVAILABLE or not FAVICON_AVAILABLE, reason="Pillow or FaviconManager not available")
def test_favicon_manager_html():
    manager = FaviconManager()
    html_out = manager.html()

    assert "apple-touch-icon.png" in html_out
    assert "favicon-32x32.png" in html_out
    assert "favicon-16x16.png" in html_out
    assert "site.webmanifest" in html_out
    assert "favicon.ico" in html_out
