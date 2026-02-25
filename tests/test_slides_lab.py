import unittest
from pathlib import Path
import tempfile
import shutil
from shared.slides_lab import SlideDeck

class TestSlideDeck(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_basic(self):
        content = "# Slide 1\nContent 1\n---\n# Slide 2\nContent 2"
        f = self.temp_path / "slides.md"
        f.write_text(content, encoding="utf-8")

        deck = SlideDeck(f)
        deck.load()

        self.assertEqual(len(deck), 2)
        self.assertIn("# Slide 1", deck.get_slide(0))
        self.assertIn("# Slide 2", deck.get_slide(1))

    def test_load_with_frontmatter(self):
        content = "---\ntitle: Test\nauthor: Me\n---\n# Slide 1\n---\n# Slide 2"
        f = self.temp_path / "slides_fm.md"
        f.write_text(content, encoding="utf-8")

        deck = SlideDeck(f)
        deck.load()

        self.assertEqual(deck.metadata.get("title"), "Test")
        self.assertEqual(len(deck), 2)
        self.assertIn("# Slide 1", deck.get_slide(0))

    def test_load_empty(self):
        f = self.temp_path / "empty.md"
        f.write_text("", encoding="utf-8")

        deck = SlideDeck(f)
        deck.load()

        self.assertEqual(len(deck), 1)
        self.assertIn("Empty Presentation", deck.get_slide(0))

    def test_file_not_found(self):
        f = self.temp_path / "nonexistent.md"
        deck = SlideDeck(f)
        with self.assertRaises(FileNotFoundError):
            deck.load()

if __name__ == '__main__':
    unittest.main()
