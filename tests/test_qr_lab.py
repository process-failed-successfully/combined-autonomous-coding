import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.qr_lab import QRLabManager, run_qr_lab_logic

class TestQRLabManager(unittest.TestCase):
    def setUp(self):
        # Patch import check for init if needed, but here we test explicit patching
        pass

    @patch("shared.qr_lab.HAS_QR", True)
    @patch("shared.qr_lab.qrcode")
    @patch("shared.qr_lab.console")
    def test_generate_ascii(self, mock_console, mock_qrcode):
        manager = QRLabManager()
        # Setup
        mock_qr_instance = MagicMock()
        mock_qrcode.QRCode.return_value = mock_qr_instance

        # Test
        manager.generate("test")

        # Assert
        mock_qr_instance.add_data.assert_called_with("test")
        mock_qr_instance.make.assert_called_with(fit=True)
        mock_qr_instance.print_ascii.assert_called_with(tty=True)
        mock_console.print.assert_called()

    @patch("shared.qr_lab.HAS_QR", True)
    @patch("shared.qr_lab.qrcode")
    @patch("shared.qr_lab.console")
    def test_generate_image(self, mock_console, mock_qrcode):
        manager = QRLabManager()
        # Setup
        mock_qr_instance = MagicMock()
        mock_img = MagicMock()
        mock_qr_instance.make_image.return_value = mock_img
        mock_qrcode.QRCode.return_value = mock_qr_instance

        output_path = Path("test.png")

        # Test
        manager.generate("test", output_path=output_path, fill_color="red", back_color="blue")

        # Assert
        mock_qr_instance.make_image.assert_called_with(fill_color="red", back_color="blue")
        mock_img.save.assert_called_with(output_path)
        mock_console.print.assert_called()

    @patch("shared.qr_lab.HAS_QR", True)
    def test_generate_wifi(self):
        manager = QRLabManager()
        # Test WPA
        ssid = "MyWiFi"
        password = "secretpassword"
        result = manager.generate_wifi(ssid, password, "WPA", False)
        self.assertEqual(result, "WIFI:S:MyWiFi;T:WPA;P:secretpassword;H:false;;")

        # Test No Pass
        result = manager.generate_wifi("OpenNet", None, "nopass", True)
        self.assertEqual(result, "WIFI:S:OpenNet;T:nopass;P:;H:true;;")

        # Test escaping
        result = manager.generate_wifi("My;WiFi", "pass:word", "WPA", False)
        self.assertEqual(result, "WIFI:S:My\;WiFi;T:WPA;P:pass\:word;H:false;;")

    @patch("shared.qr_lab.HAS_QR", False)
    def test_missing_dependency(self):
        with self.assertRaises(ImportError):
            QRLabManager()

if __name__ == "__main__":
    unittest.main()
