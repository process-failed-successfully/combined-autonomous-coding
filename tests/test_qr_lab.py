# tests/test_qr_lab.py
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add parent dir to path to find shared
sys.path.append(str(Path(__file__).parent.parent))

from shared.qr_lab import QRLabManager

class TestQRLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = QRLabManager()

    def test_generate_wifi(self):
        # WPA
        wifi = self.manager.generate_wifi("MySSID", "secret", "WPA", False)
        self.assertEqual(wifi, "WIFI:S:MySSID;T:WPA;P:secret;H:false;;")

        # WEP hidden
        wifi = self.manager.generate_wifi("MySSID", "12345", "WEP", True)
        self.assertEqual(wifi, "WIFI:S:MySSID;T:WEP;P:12345;H:true;;")

        # No Pass
        wifi = self.manager.generate_wifi("FreeWifi")
        self.assertEqual(wifi, "WIFI:S:FreeWifi;T:nopass;P:;H:false;;")

        # Special chars
        wifi = self.manager.generate_wifi("Foo;Bar", "Baz:Quux")
        self.assertEqual(wifi, "WIFI:S:Foo\\;Bar;T:WPA;P:Baz\\:Quux;H:false;;")

    def test_generate_email(self):
        email = self.manager.generate_email("test@example.com", "Hello World", "This is a test.")
        self.assertEqual(email, "mailto:test@example.com?subject=Hello%20World&body=This%20is%20a%20test.")

        email = self.manager.generate_email("test@example.com")
        self.assertEqual(email, "mailto:test@example.com")

    def test_generate_sms(self):
        sms = self.manager.generate_sms("+1234567890", "Hello there")
        self.assertEqual(sms, "sms:+1234567890?body=Hello%20there")

        sms = self.manager.generate_sms("123")
        self.assertEqual(sms, "sms:123")

    def test_generate_geo(self):
        geo = self.manager.generate_geo(37.7749, -122.4194)
        self.assertEqual(geo, "geo:37.7749,-122.4194")

    @patch("shared.qr_lab.qrcode.QRCode")
    def test_generate_ascii(self, mock_qr_cls):
        mock_qr = MagicMock()
        mock_qr_cls.return_value = mock_qr

        # Mock print_ascii to write to the file-like object passed to 'out'
        def side_effect(out=None, tty=False):
            if out:
                out.write("##  ##\n  ##  ")

        mock_qr.print_ascii.side_effect = side_effect

        ascii_art = self.manager.generate_ascii("test")
        self.assertEqual(ascii_art, "##  ##\n  ##  ")
