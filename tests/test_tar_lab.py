import unittest
import tempfile
from pathlib import Path
from shared.tar_lab import TarManager


class TestTarLab(unittest.TestCase):

    def setUp(self):
        self.manager = TarManager()
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_create_and_extract_tar(self):
        # Create some test files
        f1 = self.root / "test1.txt"
        f1.write_text("hello", encoding="utf-8")

        f2 = self.root / "test2.txt"
        f2.write_text("world", encoding="utf-8")

        # Create tar
        tar_path = self.root / "archive.tar"
        self.manager.create([f1, f2], tar_path)

        self.assertTrue(tar_path.exists())

        # List contents
        contents = self.manager.list_contents(tar_path)
        self.assertIn("test1.txt", contents)
        self.assertIn("test2.txt", contents)

        # Extract
        extract_dir = self.root / "extracted"
        self.manager.extract(tar_path, extract_dir)

        self.assertTrue((extract_dir / "test1.txt").exists())
        self.assertEqual((extract_dir / "test1.txt").read_text(encoding="utf-8"), "hello")

        self.assertTrue((extract_dir / "test2.txt").exists())
        self.assertEqual((extract_dir / "test2.txt").read_text(encoding="utf-8"), "world")

    def test_create_with_compression(self):
        f1 = self.root / "test1.txt"
        f1.write_text("data", encoding="utf-8")

        tar_path = self.root / "archive.tar.gz"
        self.manager.create([f1], tar_path, compression="gz")

        self.assertTrue(tar_path.exists())

        contents = self.manager.list_contents(tar_path)
        self.assertIn("test1.txt", contents)

    def test_create_empty_input(self):
        with self.assertRaises(ValueError):
            self.manager.create([], self.root / "out.tar")

    def test_extract_invalid_file(self):
        invalid_file = self.root / "nonexistent.tar"
        with self.assertRaises(FileNotFoundError):
            self.manager.extract(invalid_file, self.root / "out")
