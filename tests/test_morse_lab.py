import unittest
import argparse
import sys
import io
import os
import wave
from pathlib import Path
from unittest.mock import patch

from shared.morse_lab import MorseLabManager, run_morse_lab_logic

class TestMorseLab(unittest.TestCase):
    def setUp(self):
        self.manager = MorseLabManager()

        # IO Capture
        self.held_stdout = io.StringIO()
        self.held_stderr = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.held_stdout
        sys.stderr = self.held_stderr

        self.test_dir = Path("mock_dir")
        self.test_dir.mkdir(exist_ok=True)
        self.audio_path = self.test_dir / "test_morse.wav"

    def tearDown(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

        if self.audio_path.exists():
            self.audio_path.unlink()
        if self.test_dir.exists():
            self.test_dir.rmdir()

    def test_encode_basic(self):
        result = self.manager.encode("SOS")
        self.assertEqual(result, "... --- ...")

    def test_encode_with_spaces(self):
        result = self.manager.encode("HELLO WORLD")
        self.assertEqual(result, ".... . .-.. .-.. --- / .-- --- .-. .-.. -..")

    def test_encode_empty(self):
        result = self.manager.encode("")
        self.assertEqual(result, "")

    def test_decode_basic(self):
        result = self.manager.decode("... --- ...")
        self.assertEqual(result, "SOS")

    def test_decode_with_slash(self):
        result = self.manager.decode(".... . .-.. .-.. --- / .-- --- .-. .-.. -..")
        self.assertEqual(result, "HELLO WORLD")

    def test_decode_with_spaces(self):
        # 3 spaces is standard for word separation if slash isn't used
        result = self.manager.decode(".... . .-.. .-.. ---   .-- --- .-. .-.. -..")
        self.assertEqual(result, "HELLO WORLD")

    def test_decode_empty(self):
        result = self.manager.decode("")
        self.assertEqual(result, "")

    def test_decode_invalid(self):
        result = self.manager.decode("........") # Doesn't exist
        self.assertEqual(result, "?")

    def test_generate_audio(self):
        success = self.manager.generate_audio("... --- ...", self.audio_path, wpm=20)
        self.assertTrue(success)
        self.assertTrue(self.audio_path.exists())

        # Verify it's a valid WAV file
        with wave.open(str(self.audio_path), 'r') as w:
            self.assertEqual(w.getnchannels(), 1)
            self.assertEqual(w.getsampwidth(), 2)
            self.assertEqual(w.getframerate(), 44100)

    def test_cli_encode(self):
        args = argparse.Namespace(text="SOS", encode=True, decode=False, audio=None)
        success = run_morse_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("... --- ...", self.held_stdout.getvalue())

    def test_cli_decode(self):
        args = argparse.Namespace(text="... --- ...", encode=False, decode=True, audio=None)
        success = run_morse_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("SOS", self.held_stdout.getvalue())

    def test_cli_auto_detect_encode(self):
        args = argparse.Namespace(text="HELLO", encode=False, decode=False, audio=None)
        success = run_morse_lab_logic(args)
        self.assertTrue(success)
        self.assertIn(".... . .-.. .-.. ---", self.held_stdout.getvalue())

    def test_cli_auto_detect_decode(self):
        args = argparse.Namespace(text="... --- ...", encode=False, decode=False, audio=None)
        success = run_morse_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("SOS", self.held_stdout.getvalue())

    def test_cli_audio_generation(self):
        args = argparse.Namespace(text="SOS", encode=False, decode=False, audio=str(self.audio_path))
        success = run_morse_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("Audio generated successfully", self.held_stdout.getvalue())
        self.assertTrue(self.audio_path.exists())

    def test_cli_no_input(self):
        args = argparse.Namespace(text="", encode=False, decode=False, audio=None)

        # Ensure stdin is simulated as a tty so it doesn't block on read
        with patch('sys.stdin.isatty', return_value=True):
            success = run_morse_lab_logic(args)

        self.assertFalse(success)
        self.assertIn("Input text required", self.held_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
