import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path
import argparse

from shared.uuid_lab import run_uuid_lab_logic

class TestUuidCli(unittest.TestCase):
    @patch("sys.stdout")
    def test_extract_cli_text(self, mock_stdout):
        args = argparse.Namespace(
            action="extract",
            text="hello 12345678-1234-4234-8234-123456789012 world",
            file=None,
            unique=False
        )

        with patch("sys.exit") as mock_exit:
            run_uuid_lab_logic(args)

            # Since mock_exit stops sys.exit(), we need to check stdout calls
            output = "".join([call[0][0] for call in mock_stdout.write.call_args_list])
            self.assertIn("12345678-1234-4234-8234-123456789012", output)

    @patch("sys.stdout")
    def test_extract_cli_file(self, mock_stdout):
        # Create temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            f.write("uuid 1: 12345678-1234-4234-8234-123456789012\n")
            f.write("uuid 2: 12345678-1234-4234-8234-123456789012\n")
            f.write("uuid 3: aaaaaaaa-1234-4234-8234-123456789012\n")
            temp_name = f.name

        args = argparse.Namespace(
            action="extract",
            text=None,
            file=temp_name,
            unique=True
        )

        try:
            with patch("sys.exit") as mock_exit:
                run_uuid_lab_logic(args)

                output = "".join([call[0][0] for call in mock_stdout.write.call_args_list])
                self.assertIn("12345678-1234-4234-8234-123456789012", output)
                self.assertIn("aaaaaaaa-1234-4234-8234-123456789012", output)
                # Ensure we only have two lines of output (plus maybe newlines)
                self.assertEqual(output.strip().count("\n"), 1)
        finally:
            os.remove(temp_name)

if __name__ == "__main__":
    unittest.main()
