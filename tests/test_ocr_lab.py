import pytest
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import json

# Ensure shared modules can be imported
sys.path.append(str(Path(__file__).parent.parent))

from shared.ocr_lab import OcrLabManager, run_ocr_lab_logic

class TestOcrLabManager(unittest.TestCase):
    def setUp(self):
        # Mock pytesseract and Image
        self.patcher_pytesseract = patch('shared.ocr_lab.pytesseract')
        self.mock_pytesseract = self.patcher_pytesseract.start()

        self.patcher_image = patch('shared.ocr_lab.Image')
        self.mock_image = self.patcher_image.start()

        self.patcher_shutil = patch('shared.ocr_lab.shutil')
        self.mock_shutil = self.patcher_shutil.start()

        # Ensure HAS_OCR is True and tesseract cmd is found
        self.mock_shutil.which.return_value = '/usr/bin/tesseract'

        # We need to force reload or patch HAS_OCR in shared.ocr_lab if possible,
        # but since it's a global variable set at import time, we might need to mock it where it's used
        # or just assume it's True if pytesseract is mockable.
        # Actually, if we mock the module in sys.modules before import, we can control it.
        # But here we already imported. Let's patch the HAS_OCR in the module.
        patch('shared.ocr_lab.HAS_OCR', True).start()

        self.manager = OcrLabManager()

    def tearDown(self):
        self.patcher_pytesseract.stop()
        self.patcher_image.stop()
        self.patcher_shutil.stop()
        patch.stopall()

    def test_extract_text(self):
        self.mock_pytesseract.image_to_string.return_value = "Hello World"

        with patch('pathlib.Path.exists', return_value=True):
            result = self.manager.extract_text(Path("test.png"))
            self.assertEqual(result, "Hello World")
            self.mock_pytesseract.image_to_string.assert_called_once()

    def test_get_data(self):
        expected_data = {"text": ["Hello", "World"], "conf": [90, 95]}
        self.mock_pytesseract.image_to_data.return_value = expected_data

        with patch('pathlib.Path.exists', return_value=True):
            result = self.manager.get_data(Path("test.png"))
            self.assertEqual(result, expected_data)
            self.mock_pytesseract.image_to_data.assert_called_once()

    def test_get_languages(self):
        expected_langs = ["eng", "fra", "deu"]
        self.mock_pytesseract.get_languages.return_value = expected_langs

        result = self.manager.get_languages()
        self.assertEqual(result, expected_langs)

class TestOcrLabCLI(unittest.TestCase):
    def setUp(self):
        self.patcher_manager = patch('shared.ocr_lab.OcrLabManager')
        self.mock_manager_class = self.patcher_manager.start()
        self.mock_manager = self.mock_manager_class.return_value

    def tearDown(self):
        self.patcher_manager.stop()

    def test_extract_action(self):
        args = MagicMock()
        args.action = "extract"
        args.file = "test.png"
        args.lang = "eng"
        args.output = None
        args.project_dir = Path(".")

        self.mock_manager.extract_text.return_value = "Extracted Text"

        with patch('builtins.print') as mock_print:
            run_ocr_lab_logic(args)
            self.mock_manager.extract_text.assert_called_with(Path("test.png"), lang="eng")
            mock_print.assert_called_with("Extracted Text")

    def test_data_action(self):
        args = MagicMock()
        args.action = "data"
        args.file = "test.png"
        args.lang = None
        args.output = None
        args.project_dir = Path(".")

        fake_data = {"text": ["foo"]}
        self.mock_manager.get_data.return_value = fake_data

        with patch('builtins.print') as mock_print:
            run_ocr_lab_logic(args)
            self.mock_manager.get_data.assert_called_with(Path("test.png"), lang=None)
            # Should print JSON
            mock_print.assert_called_with(json.dumps(fake_data, indent=2))

    def test_langs_action(self):
        args = MagicMock()
        args.action = "langs"
        args.project_dir = Path(".")

        self.mock_manager.get_languages.return_value = ["eng", "spa"]

        with patch('builtins.print') as mock_print:
            run_ocr_lab_logic(args)
            self.mock_manager.get_languages.assert_called_once()

from unittest.mock import patch, MagicMock
from pathlib import Path
from main import run_ocr_lab
import argparse
from shared.tui_ocr import OcrLabTab

@patch('shared.ocr_lab.OcrLabManager')
def test_run_ocr_lab_cli_extract(mock_manager_class, tmp_path):
    mock_manager = MagicMock()
    mock_manager_class.return_value = mock_manager
    mock_manager.extract_text.return_value = "Mocked OCR Text"

    args = argparse.Namespace(
        command="ocr-lab",
        action="extract",
        file="test.png",
        lang="eng",
        output=str(tmp_path / "output.txt"),
        tui=False,
        project_dir=tmp_path
    )

    with pytest.raises(SystemExit) as e:
        run_ocr_lab(args)

    assert e.value.code == 0
    mock_manager.extract_text.assert_called_once()
    assert (tmp_path / "output.txt").read_text() == "Mocked OCR Text"

@patch('shared.ocr_lab.OcrLabManager')
def test_run_ocr_lab_cli_data(mock_manager_class, tmp_path):
    mock_manager = MagicMock()
    mock_manager_class.return_value = mock_manager
    mock_manager.get_data.return_value = {"text": ["Mocked", "Data"]}

    args = argparse.Namespace(
        command="ocr-lab",
        action="data",
        file="test.png",
        lang="eng",
        output=str(tmp_path / "output.json"),
        tui=False,
        project_dir=tmp_path
    )

    with pytest.raises(SystemExit) as e:
        run_ocr_lab(args)

    assert e.value.code == 0
    mock_manager.get_data.assert_called_once()

    import json
    with open(tmp_path / "output.json", "r") as f:
        data = json.load(f)
    assert data == {"text": ["Mocked", "Data"]}

@patch('shared.ocr_lab.OcrLabManager')
def test_run_ocr_lab_cli_langs(mock_manager_class, capsys):
    mock_manager = MagicMock()
    mock_manager_class.return_value = mock_manager
    mock_manager.get_languages.return_value = ["eng", "fra"]

    args = argparse.Namespace(
        command="ocr-lab",
        action="langs",
        file=None,
        lang=None,
        output=None,
        tui=False,
        project_dir=Path(".")
    )

    with pytest.raises(SystemExit) as e:
        run_ocr_lab(args)

    assert e.value.code == 0
    mock_manager.get_languages.assert_called_once()
    captured = capsys.readouterr()
    assert "eng" in captured.out
    assert "fra" in captured.out

@patch('main.run_ocr_lab')
def test_run_ocr_lab_tui(mock_run):
    args = argparse.Namespace(command="ocr-lab", action="tui", tui=True, project_dir=Path("."))
    pass

@pytest.mark.asyncio
async def test_ocr_lab_tab_components():
    """Test that the OCR tab initializes correctly."""
    tab = OcrLabTab(project_dir=Path("."))
    assert tab.project_dir == Path(".")
    assert tab.manager is not None
