import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from shared.favicon_lab import FaviconManager, run_favicon_lab_logic

def test_favicon_html():
    manager = FaviconManager()
    html = manager.html()
    assert 'apple-touch-icon' in html
    assert 'favicon-32x32.png' in html
    assert 'site.webmanifest' in html

@patch('shared.favicon_lab.PILLOW_AVAILABLE', True)
@patch('shared.favicon_lab.Image')
@patch('builtins.open', new_callable=mock_open)
@patch('shared.favicon_lab.json.dump')
@patch('shared.favicon_lab.Path.mkdir')
@patch('shared.favicon_lab.Path.is_file', return_value=True)
def test_favicon_generate(mock_is_file, mock_mkdir, mock_json_dump, mock_file, mock_image):
    manager = FaviconManager()

    mock_img = MagicMock()
    mock_img.width = 100
    mock_img.height = 100
    mock_img.convert.return_value = mock_img
    mock_img.copy.return_value = mock_img
    mock_img.resize.return_value = mock_img

    mock_image.open.return_value.__enter__.return_value = mock_img

    success = manager.generate("dummy.png", "out_dir")

    assert success is True
    assert mock_mkdir.called
    assert mock_json_dump.called
    assert mock_img.save.call_count >= 5 # 1 ICO, 2 PNG (192, 512), 1 apple, 2 PNG (16, 32)
