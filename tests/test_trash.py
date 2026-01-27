import unittest
import tempfile
import shutil
import os
from pathlib import Path
from shared.trash import TrashManager

class TestTrashManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.manager = TrashManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_trash_file(self):
        # Create a file
        f = self.project_dir / "test_file.txt"
        f.write_text("content")

        # Trash it
        trash_id = self.manager.trash(f)

        self.assertFalse(f.exists())
        self.assertTrue((self.manager.trash_dir / trash_id / "test_file.txt").exists())
        self.assertTrue((self.manager.trash_dir / trash_id / "manifest.json").exists())

    def test_restore_file(self):
        f = self.project_dir / "restore_me.txt"
        f.write_text("data")
        trash_id = self.manager.trash(f)

        self.manager.restore(trash_id)
        self.assertTrue(f.exists())
        self.assertEqual(f.read_text(), "data")
        self.assertFalse((self.manager.trash_dir / trash_id).exists())

    def test_list_trash(self):
        f1 = self.project_dir / "f1.txt"
        f1.touch()
        self.manager.trash(f1)

        items = self.manager.list_trash()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["filename"], "f1.txt")

    def test_empty_trash(self):
        f1 = self.project_dir / "f1.txt"
        f1.touch()
        self.manager.trash(f1)

        self.manager.empty_trash()
        items = self.manager.list_trash()
        self.assertEqual(len(items), 0)

    def test_restore_conflict(self):
        f = self.project_dir / "conflict.txt"
        f.write_text("original")
        trash_id = self.manager.trash(f)

        # Recreate file
        f.write_text("new")

        with self.assertRaises(FileExistsError):
            self.manager.restore(trash_id)

    def test_trash_dir(self):
        d = self.project_dir / "mydir"
        d.mkdir()
        (d / "sub").touch()

        trash_id = self.manager.trash(d)
        self.assertFalse(d.exists())

        self.manager.restore(trash_id)
        self.assertTrue(d.exists())
        self.assertTrue((d / "sub").exists())
