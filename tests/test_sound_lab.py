import unittest
import shutil
import tempfile
from pathlib import Path
from shared.sound_lab import SoundLabManager

class TestSoundLabManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = SoundLabManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_get_tone_samples(self):
        samples = self.manager.get_tone_samples(440, 0.1, "sine")
        self.assertIsInstance(samples, list)
        self.assertTrue(len(samples) > 0)
        self.assertIsInstance(samples[0], float)
        # Check normalization approx
        for s in samples:
            self.assertTrue(-1.0 <= s <= 1.0)

    def test_get_noise_samples(self):
        samples = self.manager.get_noise_samples("white", 0.1)
        self.assertTrue(len(samples) > 0)

    def test_get_dtmf_samples(self):
        samples = self.manager.get_dtmf_samples("123")
        self.assertTrue(len(samples) > 0)

    def test_get_morse_samples(self):
        samples = self.manager.get_morse_samples("SOS")
        self.assertTrue(len(samples) > 0)

    def test_generate_tone_file(self):
        output = self.test_dir / "test_tone.wav"
        path = self.manager.generate_tone(440, 0.1, output_path=str(output))
        self.assertTrue(path.exists())
        self.assertTrue(path.stat().st_size > 0)

if __name__ == '__main__':
    unittest.main()
