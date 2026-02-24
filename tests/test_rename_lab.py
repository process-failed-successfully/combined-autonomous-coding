import unittest
import tempfile
import shutil
from pathlib import Path
from shared.rename_lab import RenameLabManager

class TestRenameLabManager(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = RenameLabManager()
        self.root = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_files(self, names):
        paths = []
        for name in names:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
            paths.append(p)
        return paths

    def test_find_files(self):
        self.create_files(["a.txt", "b.txt", "sub/c.txt"])
        files = self.manager.find_files(self.root, "*.txt")
        self.assertEqual(len(files), 2)

        files_rec = self.manager.find_files(self.root, "*.txt", recursive=True)
        self.assertEqual(len(files_rec), 3)

    def test_calculate_renames_regex(self):
        files = self.create_files(["image_01.jpg", "image_02.jpg", "other.txt"])
        # Rename image_XX.jpg to img_XX.png
        renames = self.manager.calculate_renames(
            files,
            search=r"image_(\d+)\.jpg",
            replace=r"img_\1.png"
        )

        self.assertEqual(len(renames), 2)
        # Check source and dest
        src_names = sorted([r[0].name for r in renames])
        dest_names = sorted([r[1].name for r in renames])
        self.assertEqual(src_names, ["image_01.jpg", "image_02.jpg"])
        self.assertEqual(dest_names, ["img_01.png", "img_02.png"])

    def test_calculate_renames_transform(self):
        files = self.create_files(["MyFile.txt", "AnotherFile.TXT"])
        renames = self.manager.calculate_renames(
            files,
            search=None,
            replace=None,
            transform="snake"
        )

        self.assertEqual(len(renames), 2)
        # MyFile.txt -> my_file.txt
        # AnotherFile.TXT -> another_file.TXT (transform only applies to stem logic I wrote)

        dest_names = sorted([r[1].name for r in renames])
        self.assertIn("my_file.txt", dest_names)
        self.assertIn("another_file.TXT", dest_names)

    def test_apply_renames_dry_run(self):
        files = self.create_files(["test.txt"])
        renames = [(files[0], self.root / "renamed.txt")]

        success = self.manager.apply_renames(renames, dry_run=True)
        self.assertTrue(success)
        self.assertTrue((self.root / "test.txt").exists())
        self.assertFalse((self.root / "renamed.txt").exists())

    def test_apply_renames_execute(self):
        files = self.create_files(["test.txt"])
        renames = [(files[0], self.root / "renamed.txt")]

        success = self.manager.apply_renames(renames, dry_run=False)
        self.assertTrue(success)
        self.assertFalse((self.root / "test.txt").exists())
        self.assertTrue((self.root / "renamed.txt").exists())

    def test_collision_detection(self):
        files = self.create_files(["a.txt", "b.txt"])
        # Try to rename 'a.txt' to 'b.txt' (which exists)
        renames = [(files[0], files[1])]

        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
             success = self.manager.apply_renames(renames, dry_run=False)

        self.assertFalse(success)
        self.assertTrue((self.root / "a.txt").exists())
        self.assertTrue((self.root / "b.txt").exists())

    def test_duplicate_destination_collision(self):
        files = self.create_files(["a.txt", "b.txt"])
        # Try to rename both to 'c.txt'
        dest = self.root / "c.txt"
        renames = [
            (files[0], dest),
            (files[1], dest)
        ]

        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
             success = self.manager.apply_renames(renames, dry_run=False)

        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
