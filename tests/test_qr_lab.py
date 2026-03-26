# tests/test_qr_lab.py
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add parent dir to path to find shared
sys.path.append(str(Path(__file__).parent.parent))

from shared.qr_lab import QRLabManager  # noqa: E402


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

    @patch("shared.qr_lab.QRLabManager.generate")
    @patch("shared.qr_lab.console.print")
    def test_run_qr_lab_logic_email(self, mock_print, mock_generate):
        from shared.qr_lab import run_qr_lab_logic

        class Args:
            action = "email"
            to = "test@example.com"
            subject = "Subj"
            body = "Msg"
            output = None

        args = Args()
        run_qr_lab_logic(args)

        mock_generate.assert_called_once_with("mailto:test@example.com?subject=Subj&body=Msg")
        mock_print.assert_called()

    @patch("shared.qr_lab.QRLabManager.generate")
    @patch("shared.qr_lab.console.print")
    def test_run_qr_lab_logic_sms(self, mock_print, mock_generate):
        from shared.qr_lab import run_qr_lab_logic

        class Args:
            action = "sms"
            phone = "+12345"
            message = "Hi"
            output = "out.png"

        args = Args()
        run_qr_lab_logic(args)

        mock_generate.assert_called_once_with("sms:+12345?body=Hi", output_path=Path("out.png"))

    @patch("shared.qr_lab.QRLabManager.generate")
    @patch("shared.qr_lab.console.print")
    def test_run_qr_lab_logic_geo(self, mock_print, mock_generate):
        from shared.qr_lab import run_qr_lab_logic

        class Args:
            action = "geo"
            lat = 10.0
            lon = 20.0
            output = None

        args = Args()
        run_qr_lab_logic(args)

        mock_generate.assert_called_once_with("geo:10.0,20.0")

    @patch("asyncio.run")
    @patch("shared.tui.AgentTUI")
    def test_run_qr_lab_logic_tui(self, mock_tui, mock_run):
        from shared.qr_lab import run_qr_lab_logic

        class Args:
            action = "tui"

        args = Args()

        mock_app = MagicMock()
        mock_tui.return_value = mock_app
        mock_app.run_async.return_value = "coro"

        run_qr_lab_logic(args)

        mock_tui.assert_called_once()
        kwargs = mock_tui.call_args.kwargs
        self.assertEqual(kwargs["initial_tab"], "tab-qr")
        mock_run.assert_called_once_with("coro")

    @patch("shared.qr_lab.QRLabManager.generate")
    def test_run_qr_lab_logic_styling(self, mock_generate):
        from shared.qr_lab import run_qr_lab_logic
        import argparse
        args = argparse.Namespace(
            action="gen",
            text="styled_test",
            output="styled.png",
            fill_color="red",
            back_color="blue",
            logo="logo.png",
            drawer="circle",
            color_mask="radial"
        )
        run_qr_lab_logic(args)
        mock_generate.assert_called_once()
        _, kwargs = mock_generate.call_args
        assert kwargs["logo"] == "logo.png"
        assert kwargs["drawer"] == "circle"
        assert kwargs["color_mask"] == "radial"
        assert kwargs["fill_color"] == "red"
        assert kwargs["back_color"] == "blue"

    @patch("shared.qr_lab.qrcode.QRCode.make_image")
    def test_create_image_styled(self, mock_make_image):
        from shared.qr_lab import QRLabManager
        import qrcode
        import qrcode.image.styledpil
        from qrcode.image.styles.moduledrawers.pil import CircleModuleDrawer
        from qrcode.image.styles.colormasks import RadialGradiantColorMask

        manager = QRLabManager()
        qr = qrcode.QRCode()
        qr.add_data("test")

        manager._create_image(
            qr,
            fill_color="red",
            back_color="blue",
            logo="dummy.png",
            drawer="circle",
            color_mask="radial"
        )

        mock_make_image.assert_called_once()
        _, kwargs = mock_make_image.call_args

        assert kwargs["image_factory"] == qrcode.image.styledpil.StyledPilImage
        assert isinstance(kwargs["module_drawer"], CircleModuleDrawer)
        assert isinstance(kwargs["color_mask"], RadialGradiantColorMask)
        assert kwargs["embeded_image_path"] == "dummy.png"
