# tests/test_qr_lab.py
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add parent dir to path to find shared
sys.path.append(str(Path(__file__).parent.parent))

from shared.qr_lab import QRLabManager  # noqa: E402
import shared.tui  # noqa: F401


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

    def test_generate_vcard(self):
        vcard = self.manager.generate_vcard(
            first_name="John",
            last_name="Doe",
            org="Acme Corp",
            title="CEO",
            phone="12345",
            email="john@example.com",
            url="https://acme.com"
        )
        self.assertIn("BEGIN:VCARD", vcard)
        self.assertIn("VERSION:3.0", vcard)
        self.assertIn("N:Doe;John;;;", vcard)
        self.assertIn("FN:John Doe", vcard)
        self.assertIn("ORG:Acme Corp", vcard)
        self.assertIn("TITLE:CEO", vcard)
        self.assertIn("TEL:12345", vcard)
        self.assertIn("EMAIL:john@example.com", vcard)
        self.assertIn("URL:https://acme.com", vcard)
        self.assertIn("END:VCARD", vcard)

        # Test minimal vcard
        vcard_minimal = self.manager.generate_vcard(first_name="Jane")
        self.assertIn("N:;Jane;;;", vcard_minimal)
        self.assertIn("FN:Jane", vcard_minimal)
        self.assertNotIn("ORG:", vcard_minimal)

    def test_decode_image(self):
        import tempfile
        import qrcode

        text_to_encode = "https://example.com/test_decode"

        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / "test_decode.png"
            # Generate the image directly bypassing the CLI wrapper method
            img = qrcode.make(text_to_encode)
            img.save(str(img_path))

            # Assert file exists
            self.assertTrue(img_path.exists())

            # Now decode it
            results = self.manager.decode_image(img_path)

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], text_to_encode)

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

    @patch("shared.qr_lab.QRLabManager.generate")
    @patch("shared.qr_lab.console.print")
    def test_run_qr_lab_logic_vcard(self, mock_print, mock_generate):
        from shared.qr_lab import run_qr_lab_logic

        class Args:
            action = "vcard"
            first_name = "Jane"
            last_name = "Smith"
            org = ""
            title = ""
            phone = ""
            email = ""
            url = ""
            output = None

        args = Args()
        run_qr_lab_logic(args)

        mock_generate.assert_called_once()
        call_args = mock_generate.call_args[0][0]
        self.assertIn("BEGIN:VCARD", call_args)
        self.assertIn("FN:Jane Smith", call_args)

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
