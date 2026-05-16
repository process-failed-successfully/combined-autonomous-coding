import pytest
from pathlib import Path
from PIL import Image
import tempfile
import sys
import argparse

from shared.favicon_lab import FaviconManager, run_favicon_lab_logic

def test_generate_favicons():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        img_path = tmp_path / "logo.png"

        # Create a valid 512x512 mock image
        img = Image.new("RGBA", (512, 512), color="red")
        with open(str(img_path), "wb") as file:
            img.save(file, format="PNG")

        manager = FaviconManager(tmp_path)
        success = manager.generate("logo.png", "out_dir")

        assert success is True
        out_dir = tmp_path / "out_dir"
        assert out_dir.is_dir()

        # Check that all expected files were created
        expected_files = [
            "favicon.ico",
            "apple-touch-icon.png",
            "favicon-32x32.png",
            "favicon-16x16.png",
            "android-chrome-192x192.png",
            "android-chrome-512x512.png",
            "site.webmanifest"
        ]

        for file in expected_files:
            file_path = out_dir / file
            assert file_path.is_file()

def test_generate_favicons_too_small():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        img_path = tmp_path / "small.png"

        # Create an invalid 256x256 mock image
        img = Image.new("RGBA", (256, 256), color="red")
        with open(str(img_path), "wb") as file:
            img.save(file, format="PNG")

        manager = FaviconManager(tmp_path)
        success = manager.generate("small.png", "out_dir")

        assert success is False
        assert not (tmp_path / "out_dir").exists()

def test_generate_favicons_missing_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manager = FaviconManager(tmp_path)
        success = manager.generate("missing.png", "out_dir")
        assert success is False

def test_html_snippet():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manager = FaviconManager(tmp_path)
        html = manager.html()

        assert "apple-touch-icon" in html
        assert "favicon-32x32.png" in html
        assert "favicon-16x16.png" in html
        assert "site.webmanifest" in html

def test_run_favicon_lab_logic_generate(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        img_path = tmp_path / "logo.png"

        img = Image.new("RGBA", (512, 512), color="blue")
        with open(str(img_path), "wb") as file:
            img.save(file, format="PNG")

        args = argparse.Namespace(
            project_dir=tmp_path,
            action="generate",
            image="logo.png",
            output="out"
        )

        success = run_favicon_lab_logic(args)
        assert success is True
        assert (tmp_path / "out" / "favicon.ico").is_file()

def test_run_favicon_lab_logic_generate_missing_image():
    with tempfile.TemporaryDirectory() as tmpdir:
        args = argparse.Namespace(
            project_dir=Path(tmpdir),
            action="generate",
            image=None,
            output="out"
        )
        success = run_favicon_lab_logic(args)
        assert success is False

def test_run_favicon_lab_logic_html(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        args = argparse.Namespace(
            project_dir=Path(tmpdir),
            action="html",
            image=None,
            output="out"
        )
        success = run_favicon_lab_logic(args)
        assert success is True
        captured = capsys.readouterr()
        assert "site.webmanifest" in captured.out
