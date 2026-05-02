import unittest
import argparse
from pathlib import Path
from unittest.mock import patch
import sys
import io

from shared.hexdump_lab import HexdumpManager, run_hexdump_lab_logic

class TestHexdumpLab(unittest.TestCase):
    def setUp(self):
        self.manager = HexdumpManager()

    def test_hexdump_basic_string(self):
        data = b"Hello world!"
        result = self.manager.hexdump(data)
        lines = result.splitlines()
        self.assertEqual(len(lines), 2)
        # Expected offset: 00000000
        # Expected hex: 48 65 6c 6c 6f 20 77 6f  72 6c 64 21
        # Expected ascii: |Hello world!|
        self.assertTrue("00000000" in lines[0])
        self.assertTrue("48 65 6c 6c 6f 20 77 6f  72 6c 64 21" in lines[0])
        self.assertTrue("|Hello world!|" in lines[0])
        # size line
        self.assertTrue("0000000c" in lines[1])

    def test_hexdump_empty(self):
        data = b""
        result = self.manager.hexdump(data)
        self.assertEqual(result, "")

    def test_hexdump_long(self):
        data = b"A" * 32
        result = self.manager.hexdump(data)
        lines = result.splitlines()
        # 32 bytes = 2 lines + 1 size line = 3 lines
        self.assertEqual(len(lines), 3)
        self.assertTrue("00000000" in lines[0])
        self.assertTrue("00000010" in lines[1])
        self.assertTrue("00000020" in lines[2])

    def test_hexdump_binary(self):
        data = bytes([0x00, 0x01, 0xff, 0xfe, 0x41])
        result = self.manager.hexdump(data)
        lines = result.splitlines()
        self.assertTrue("00 01 ff fe 41" in lines[0])
        self.assertTrue("|....A|" in lines[0])

    def test_hexdump_offset_and_length(self):
        data = b"0123456789ABCDEF"
        # We only want to dump a portion, starting at a mock offset
        result = self.manager.hexdump(data, offset=0x100, length=8)
        lines = result.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue("00000100" in lines[0])
        self.assertTrue("00000108" in lines[1])
        self.assertTrue("|01234567|" in lines[0])

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_text_args(self, mock_stdout):
        args = argparse.Namespace(
            file=None,
            text="Hello",
            offset=0,
            length=-1
        )
        success = run_hexdump_lab_logic(args)
        self.assertTrue(success)
        output = mock_stdout.getvalue()
        self.assertTrue("48 65 6c 6c 6f" in output)
        self.assertTrue("|Hello|" in output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_file_args(self, mock_stdout):
        # Create a temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"File data")
            temp_path = f.name

        args = argparse.Namespace(
            file=temp_path,
            text=None,
            offset=0,
            length=-1
        )
        try:
            success = run_hexdump_lab_logic(args)
            self.assertTrue(success)
            output = mock_stdout.getvalue()
            self.assertTrue("|File data|" in output)
        finally:
            Path(temp_path).unlink()

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_cli_missing_args(self, mock_stderr):
        args = argparse.Namespace(
            file=None,
            text=None,
            offset=0,
            length=-1
        )
        # Using patch to simulate isatty returning True (no piped data)
        with patch("sys.stdin.isatty", return_value=True):
            success = run_hexdump_lab_logic(args)
            self.assertFalse(success)
            self.assertTrue("Must provide --file, --text, or pipe data" in mock_stderr.getvalue())

if __name__ == "__main__":
    unittest.main()
