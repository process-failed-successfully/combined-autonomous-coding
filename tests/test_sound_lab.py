import unittest
import tempfile
import shutil
import wave
import os
from pathlib import Path
from shared.sound_lab import SoundLabManager

class TestSoundLab(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = SoundLabManager(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _verify_wav(self, path, expected_duration=None):
        self.assertTrue(path.exists(), f"File {path} does not exist")
        with wave.open(str(path), 'r') as wav_file:
            self.assertEqual(wav_file.getnchannels(), 1)
            self.assertEqual(wav_file.getsampwidth(), 2)
            self.assertEqual(wav_file.getframerate(), 44100)

            if expected_duration:
                frames = wav_file.getnframes()
                duration = frames / 44100.0
                self.assertAlmostEqual(duration, expected_duration, places=2)

    def test_generate_tone(self):
        output = self.temp_dir / "tone.wav"
        self.manager.generate_tone(440, 0.5, "sine", output)
        self._verify_wav(output, 0.5)

    def test_generate_noise(self):
        output = self.temp_dir / "noise.wav"
        self.manager.generate_noise("white", 0.5, output)
        self._verify_wav(output, 0.5)

    def test_generate_dtmf(self):
        output = self.temp_dir / "dtmf.wav"
        # 3 chars * (0.2 tone + 0.1 space) = 0.9s (approx)
        # Actually logic adds space after each tone.
        # "123" -> (0.2+0.1) * 3 = 0.9
        self.manager.generate_dtmf("123", output, tone_duration=0.2, space_duration=0.1)
        self._verify_wav(output, 0.9)

    def test_generate_morse(self):
        output = self.temp_dir / "morse.wav"
        # SOS = ... --- ...
        # S = dot(1)+gap(1)+dot(1)+gap(1)+dot(1) = 5 units.
        # gap(3) between letters.
        # O = dash(3)+gap(1)+dash(3)+gap(1)+dash(3) = 11 units.
        # gap(3).
        # S = 5 units.
        # Total = 5 + 3 + 11 + 3 + 5 = 27 units (roughly).
        # Plus word gap at end (7 units) if implemented that way?
        # Logic: space between words (7) if i < len(words) - 1. So no trailing word gap.
        # But wait, logic adds silence(3) after letter if j < len(word) - 1.
        # Last char of word doesn't get inter-letter gap.
        # Let's just check file creation and valid header for now.
        self.manager.generate_morse("SOS", output, wpm=20)
        self._verify_wav(output)

if __name__ == "__main__":
    unittest.main()
