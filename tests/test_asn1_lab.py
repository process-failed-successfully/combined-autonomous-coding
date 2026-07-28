import unittest
from unittest.mock import patch, MagicMock
import base64
from textual.widgets import TextArea, RichLog, Select
from shared.asn1_lab import Asn1LabManager
from shared.tui_asn1 import Asn1LabTab
from textual.app import App, ComposeResult


class DummyApp(App[None]):
    def compose(self) -> ComposeResult:
        yield Asn1LabTab()


class TestAsn1LabManager(unittest.TestCase):
    def setUp(self):
        self.manager = Asn1LabManager()

    def test_decode_hex(self):
        # A simple ASN.1 Sequence with two integers (1, 2)
        hex_data = "3006020101020102"
        result = self.manager.decode(hex_data, input_format="hex")
        self.assertTrue(result["success"])
        self.assertIn("SequenceOf", result["output"])
        self.assertIn("1 2", result["output"])

    def test_decode_base64(self):
        hex_data = "3006020101020102"
        b64_data = base64.b64encode(bytes.fromhex(hex_data)).decode()
        result = self.manager.decode(b64_data, input_format="base64")
        self.assertTrue(result["success"])
        self.assertIn("SequenceOf", result["output"])
        self.assertIn("1 2", result["output"])

    def test_decode_pem(self):
        hex_data = "3006020101020102"
        b64_data = base64.b64encode(bytes.fromhex(hex_data)).decode()
        pem_data = f"-----BEGIN ASN1-----\n{b64_data}\n-----END ASN1-----\n"
        result = self.manager.decode(pem_data, input_format="pem")
        self.assertTrue(result["success"])
        self.assertIn("SequenceOf", result["output"])
        self.assertIn("1 2", result["output"])

    def test_decode_auto_detect_pem(self):
        hex_data = "3006020101020102"
        b64_data = base64.b64encode(bytes.fromhex(hex_data)).decode()
        pem_data = f"-----BEGIN ASN1-----\n{b64_data}\n-----END ASN1-----\n"
        result = self.manager.decode(pem_data, input_format="auto")
        self.assertTrue(result["success"])
        self.assertIn("SequenceOf", result["output"])

    def test_decode_invalid_data(self):
        result = self.manager.decode("not-valid-hex-or-base64-!!!!", input_format="hex")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_decode_empty(self):
        result = self.manager.decode("", input_format="auto")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Empty payload provided.")


class TestAsn1LabTui(unittest.IsolatedAsyncioTestCase):
    async def test_tui_decode_success(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Locate widgets
            input_area = app.query_one("#asn1-input", TextArea)
            format_select = app.query_one("#asn1-format", Select)
            output_log = app.query_one("#asn1-output", RichLog)

            # Set input
            input_area.text = "3006020101020102"
            format_select.value = "hex"

            # Mock the write function of RichLog
            with patch.object(RichLog, "write", new_callable=MagicMock) as mock_write:
                with patch.object(RichLog, "clear", new_callable=MagicMock) as mock_clear:
                    await pilot.click("#btn-asn1-decode")
                    await pilot.pause()

                    # Verify successful output was logged
                    mock_clear.assert_called_once()
                    self.assertTrue(any("Decoding Successful" in str(call.args) for call in mock_write.call_args_list))
                    self.assertTrue(any("SequenceOf" in str(call.args) for call in mock_write.call_args_list))

    async def test_tui_decode_empty(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_area = app.query_one("#asn1-input", TextArea)
            input_area.text = "   \n "

            with patch.object(RichLog, "write", new_callable=MagicMock) as mock_write:
                await pilot.click("#btn-asn1-decode")
                await pilot.pause()

                self.assertTrue(any("Input cannot be empty" in str(call.args) for call in mock_write.call_args_list))

    async def test_tui_decode_error(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_area = app.query_one("#asn1-input", TextArea)
            format_select = app.query_one("#asn1-format", Select)

            input_area.text = "invalid_hex"
            format_select.value = "hex"

            with patch.object(RichLog, "write", new_callable=MagicMock) as mock_write:
                await pilot.click("#btn-asn1-decode")
                await pilot.pause()

                self.assertTrue(any("Error" in str(call.args) for call in mock_write.call_args_list))


if __name__ == "__main__":
    unittest.main()
