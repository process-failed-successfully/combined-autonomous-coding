import pytest
from shared.magic_decode_lab import MagicDecodeManager, run_magic_decode_lab_logic
import argparse
from unittest.mock import patch
import sys
import io

class TestMagicDecodeLab:
    def setup_method(self):
        self.manager = MagicDecodeManager()

    def test_decode_base64(self):
        encoded = "SGVsbG8gV29ybGQh"
        res = self.manager.decode(encoded)
        assert "Base64" in res
        assert res["Base64"] == "Hello World!"

    def test_decode_hex(self):
        encoded = "48656c6c6f20576f726c64"
        res = self.manager.decode(encoded)
        assert "Hex" in res
        assert res["Hex"] == "Hello World"

    def test_decode_url(self):
        encoded = "Hello%20World%21"
        res = self.manager.decode(encoded)
        assert "URL Encoded" in res
        assert res["URL Encoded"] == "Hello World!"

    def test_decode_html(self):
        encoded = "&lt;hello&gt;"
        res = self.manager.decode(encoded)
        assert "HTML Entities" in res
        assert res["HTML Entities"] == "<hello>"

    def test_decode_rot13(self):
        encoded = "Uryyb Jbeyq"
        res = self.manager.decode(encoded)
        assert "ROT13" in res
        assert res["ROT13"] == "Hello World"

    def test_decode_binary(self):
        encoded = "0100100001100101011011000110110001101111"
        res = self.manager.decode(encoded)
        assert "Binary" in res
        assert res["Binary"] == "Hello"

    def test_decode_octal(self):
        encoded = "110 145 154 154 157"
        res = self.manager.decode(encoded)
        assert "Octal" in res
        assert res["Octal"] == "Hello"

    def test_decode_unix_timestamp(self):
        encoded = "1609459200"
        res = self.manager.decode(encoded)
        assert "Unix Timestamp" in res
        assert "2021" in res["Unix Timestamp"]

    def test_decode_json(self):
        encoded = '{"key": "value"}'
        res = self.manager.decode(encoded)
        assert "JSON" in res
        assert '"key": "value"' in res["JSON"]

    def test_run_magic_decode_lab_logic(self):
        args = argparse.Namespace(text="SGVsbG8=")

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with patch('shared.magic_decode_lab.console.print') as mock_print:
                success = run_magic_decode_lab_logic(args)
                assert success is True
                mock_print.assert_any_call("Hello")

    def test_run_magic_decode_lab_logic_empty(self):
        # We need a string that won't trigger ANY decoding, not even ROT13 (which triggers on alpha) or Unix Timestamp.
        args = argparse.Namespace(text="!@#$%^&*()")

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with patch('shared.magic_decode_lab.console.print') as mock_print:
                success = run_magic_decode_lab_logic(args)
                assert success is True
                # Should print a message about no decodings found
                mock_print.assert_any_call("[yellow]No decodings found. The string might not be in a recognized format or is just plain text.[/yellow]")
