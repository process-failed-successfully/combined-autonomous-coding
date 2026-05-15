import pytest
import shutil
from pathlib import Path
from PIL import Image
from shared.favicon_lab import FaviconManager

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def dummy_image(temp_dir):
    img_path = temp_dir / "logo.png"
    # Create a 512x512 dummy image
    img = Image.new("RGBA", (512, 512), color="red")
    img.save(img_path)
    return img_path

def test_generate_favicons_success(temp_dir, dummy_image):
    manager = FaviconManager()
    output_dir = temp_dir / "out"

    success, msg = manager.generate(str(dummy_image), str(output_dir))
    assert success is True
    assert "Successfully" in msg

    # Check that required files exist
    expected_files = [
        "favicon.ico",
        "favicon-16x16.png",
        "favicon-32x32.png",
        "apple-touch-icon.png",
        "android-chrome-192x192.png",
        "android-chrome-512x512.png",
        "site.webmanifest"
    ]

    for f in expected_files:
        p = output_dir / f
        assert p.is_file(), f"{f} was not generated."

def test_generate_favicons_missing_input(temp_dir):
    manager = FaviconManager()
    output_dir = temp_dir / "out"

    success, msg = manager.generate(str(temp_dir / "missing.png"), str(output_dir))
    assert success is False
    assert "Input image not found" in msg

def test_get_html():
    manager = FaviconManager()
    html = manager.get_html()
    assert "apple-touch-icon" in html
    assert "site.webmanifest" in html
    assert "favicon-32x32.png" in html
    assert "favicon-16x16.png" in html

def test_pillow_missing(monkeypatch, temp_dir, dummy_image):
    # Simulate missing Pillow by forcing ImportError in FaviconManager init
    real_import = __import__
    def mock_import(*args, **kwargs):
        if args[0] == "PIL":
            raise ImportError("No module named PIL")
        return real_import(*args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)

    # Import locally to trigger the monkeypatched import logic
    from shared.favicon_lab import FaviconManager
    manager = FaviconManager()

    assert manager.pillow_available is False

    success, msg = manager.generate(str(dummy_image), str(temp_dir / "out"))
    assert success is False
    assert "Pillow is not installed" in msg
