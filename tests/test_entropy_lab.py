import unittest
import argparse
from unittest.mock import patch
import io
import os
import tempfile
from shared.entropy_lab import EntropyLabManager, run_entropy_lab_logic


class TestEntropyLab(unittest.TestCase):
    def setUp(self):
        self.manager = EntropyLabManager()

    def test_calculate_entropy(self):
        # Empty data
        self.assertEqual(self.manager.calculate_entropy(b""), 0.0)
        # Single byte
        self.assertEqual(self.manager.calculate_entropy(b"A" * 100), 0.0)
        # Two alternating bytes (equal distribution)
        self.assertEqual(self.manager.calculate_entropy(b"AB" * 50), 1.0)
        # Random / Max Entropy for 256 bytes (0-255)
        self.assertAlmostEqual(self.manager.calculate_entropy(bytes(range(256))), 8.0, places=4)

    def test_analyze_data(self):
        result = self.manager.analyze_data(b"A" * 100)
        self.assertEqual(result["length"], 100)
        self.assertEqual(result["entropy"], 0.0)
        self.assertEqual(result["assessment"], "Low entropy (highly repetitive or simple text)")

        result = self.manager.analyze_data(b"")
        self.assertEqual(result["assessment"], "Empty data")

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_text_args(self, mock_stdout):
        args = argparse.Namespace(text="ABAB", file=None)
        success = run_entropy_lab_logic(args)
        self.assertTrue(success)
        output = mock_stdout.getvalue()
        self.assertIn("Size: 4 bytes", output)
        self.assertIn("Entropy: 1.0000", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_file_args(self, mock_stdout):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"ABAB")
            temp_path = f.name

        args = argparse.Namespace(text=None, file=temp_path)
        try:
            success = run_entropy_lab_logic(args)
            self.assertTrue(success)
            output = mock_stdout.getvalue()
            self.assertIn("Size: 4 bytes", output)
            self.assertIn("Entropy: 1.0000", output)
        finally:
            os.remove(temp_path)

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_cli_missing_args(self, mock_stderr):
        args = argparse.Namespace(text=None, file=None)
        # patch isatty to True to simulate terminal (not pipe)
        with patch("sys.stdin.isatty", return_value=True):
            success = run_entropy_lab_logic(args)
            self.assertFalse(success)
            self.assertIn("Must provide --text, --file, or pipe data", mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
