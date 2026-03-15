import unittest
from pathlib import Path
import tempfile
import shutil

try:
    from PIL import Image
except ImportError:
    pass

from shared.image_lab import ImageLabManager, HAS_PIL


@unittest.skipIf(not HAS_PIL, "Pillow library is not installed. Please run: pip install Pillow")
class TestFavicon(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.tmp_dir)
        self.manager = ImageLabManager(self.project_dir)

        if HAS_PIL:
            # Create a dummy 800x600 image to also test cropping
            self.input_image = self.project_dir / "input.png"
            img = Image.new("RGB", (800, 600), "red")
            img.save(self.input_image)

            self.output_dir = self.project_dir / "favicons"

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_generate_favicon(self):
        if not HAS_PIL:
            self.skipTest("Pillow not installed")

        generated = self.manager.generate_favicon(self.input_image, self.output_dir)
        self.assertTrue(self.output_dir.exists())
        self.assertGreater(len(generated), 0)

        expected_files = [
            "favicon.ico",
            "apple-touch-icon.png",
            "android-chrome-192x192.png",
            "android-chrome-512x512.png",
            "favicon-32x32.png",
            "favicon-16x16.png"
        ]

        generated_names = [p.name for p in generated]
        for name in expected_files:
            self.assertIn(name, generated_names)
            self.assertTrue((self.output_dir / name).exists())


if __name__ == '__main__':
    unittest.main()
