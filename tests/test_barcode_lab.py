import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.barcode_lab import BarcodeLabManager, run_barcode_lab_logic
import barcode

class TestBarcodeLabManager:
    def test_get_supported_formats(self):
        manager = BarcodeLabManager()
        formats = manager.get_supported_formats()
        assert "ean13" in formats
        assert "code39" in formats

    @patch("barcode.writer.ImageWriter")
    def test_generate_success(self, mock_writer, tmp_path):
        manager = BarcodeLabManager()

        # We need to mock the save method of the barcode instance itself
        mock_barcode_instance = MagicMock()
        mock_barcode_instance.save.return_dict = None
        # the save method returns the path it saved to
        mock_barcode_instance.save.return_value = str(tmp_path / "test_barcode.png")

        with patch("barcode.get_barcode_class", return_value=lambda data, writer: mock_barcode_instance):
            success, msg = manager.generate("123456789012", "ean13", tmp_path / "test_barcode")

        assert success is True
        assert "Barcode saved to " in msg
        mock_barcode_instance.save.assert_called_once_with(str(tmp_path / "test_barcode"))

    def test_generate_unsupported_type(self, tmp_path):
        manager = BarcodeLabManager()
        with pytest.raises(ValueError, match="Unsupported barcode type:"):
            manager.generate("12345", "invalid_type", tmp_path / "test")

    def test_validate_success(self):
        manager = BarcodeLabManager()
        # EAN13 requires 12 or 13 digits. The library calculates checksum if 12.
        success, msg = manager.validate("123456789012", "ean13")
        assert success is True
        assert "valid" in msg

    def test_validate_failure(self):
        manager = BarcodeLabManager()
        # Invalid data for EAN13 (letters)
        success, msg = manager.validate("invalid_data", "ean13")
        assert success is False
        assert "valid" not in msg.lower() or success is False

class TestBarcodeLabCLI:
    @patch("shared.barcode_lab.Console.print")
    def test_list_action(self, mock_print):
        args = MagicMock()
        args.action = "list"
        run_barcode_lab_logic(args)

        mock_print.assert_any_call("[bold]Supported Barcode Formats:[/bold]")
        # It should print ean13
        assert any("ean13" in call_args[0][0] for call_args in mock_print.call_args_list)

    @patch("shared.barcode_lab.BarcodeLabManager.generate")
    @patch("shared.barcode_lab.Console.print")
    def test_generate_action(self, mock_print, mock_generate):
        mock_generate.return_value = (True, "Saved")
        args = MagicMock()
        args.action = "generate"
        args.data = "12345"
        args.type = "code39"
        args.output = "out"

        run_barcode_lab_logic(args)
        mock_generate.assert_called_once_with("12345", "code39", Path("out"))
        mock_print.assert_any_call("[green]✅ Saved[/green]")

    @patch("shared.barcode_lab.BarcodeLabManager.validate")
    @patch("shared.barcode_lab.Console.print")
    def test_validate_action(self, mock_print, mock_validate):
        mock_validate.return_value = (True, "Valid")
        args = MagicMock()
        args.action = "validate"
        args.data = "12345"
        args.type = "code39"

        run_barcode_lab_logic(args)
        mock_validate.assert_called_once_with("12345", "code39")
        mock_print.assert_any_call("[green]✅ Valid[/green]")
