import unittest
from unittest.mock import MagicMock
import sys
import tempfile
from pathlib import Path
import pytest

# Add repo root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from shared.fs_lab import FsLabManager


class TestFsLabManager(unittest.TestCase):

    def setUp(self):
        # Create a temp directory structure for testing
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.test_dir.name)

        # Create some files
        self.file1 = self.root / "file1.txt"
        self.file1.write_text("content1")

        self.file2 = self.root / "file2.txt"
        self.file2.write_text("content2")

        self.subdir = self.root / "subdir"
        self.subdir.mkdir()

        self.file3 = self.subdir / "file3.log"
        self.file3.write_text("content1")  # Duplicate content of file1

        self.empty_dir = self.root / "empty_dir"
        self.empty_dir.mkdir()

        self.tmp_file = self.root / "test.tmp"
        self.tmp_file.write_text("temp")

        self.manager = FsLabManager(console=MagicMock())

    def tearDown(self):
        self.test_dir.cleanup()

    def test_info(self):
        info = self.manager.get_info(self.file1)
        self.assertEqual(info['name'], "file1.txt")
        self.assertEqual(info['type'], "File")
        self.assertEqual(info['size'], 8)  # "content1" is 8 bytes
        # Checking if mime_type works (might vary by system)
        self.assertIn("text/plain", str(info.get('mime_type')))

    def test_find_name(self):
        results = self.manager.find(self.root, name="*.txt")
        names = sorted([p.name for p in results])
        self.assertEqual(names, ["file1.txt", "file2.txt"])

    def test_find_size(self):
        # file1 is 8 bytes.
        # >5B should find it.
        results = self.manager.find(self.root, size=">5B")
        self.assertIn(self.file1, results)

        # >10B should not.
        results = self.manager.find(self.root, size=">10B")
        self.assertNotIn(self.file1, results)

    def test_find_content(self):
        results = self.manager.find(self.root, content="content2")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "file2.txt")

    def test_dedup(self):
        # file1 and file3 have same content ("content1")
        duplicates = self.manager.dedup(self.root, delete=False)
        self.assertEqual(len(duplicates), 1)  # One group
        paths = list(duplicates.values())[0]
        self.assertEqual(len(paths), 2)
        names = sorted([p.name for p in paths])
        self.assertEqual(names, ["file1.txt", "file3.log"])

    def test_clean_dry_run(self):
        stats = self.manager.clean(self.root, dry_run=True)
        self.assertTrue(self.empty_dir.exists())
        self.assertTrue(self.tmp_file.exists())
        self.assertGreater(stats['dirs'], 0)  # Should find empty_dir
        self.assertGreater(stats['files'], 0)  # Should find .tmp

    def test_clean_force(self):
        self.manager.clean(self.root, dry_run=False)
        self.assertFalse(self.empty_dir.exists())
        self.assertFalse(self.tmp_file.exists())
        self.assertTrue(self.file1.exists())

    def test_shred(self):
        shred_target = self.root / "shred_me.txt"
        shred_target.write_text("secret")

        success = self.manager.shred(shred_target, passes=1)
        self.assertTrue(success)
        self.assertFalse(shred_target.exists())

    def test_shred_not_exist(self):
        shred_target = self.root / "does_not_exist.txt"
        success = self.manager.shred(shred_target, passes=1)
        self.assertFalse(success)

    def test_get_info_not_exist(self):
        with self.assertRaises(FileNotFoundError):
            self.manager.get_info(self.root / "does_not_exist.txt")

    def test_find_with_multiple_filters(self):
        results = self.manager.find(self.root, ftype="f", size="<1M", mtime="<1d", content="content1")
        names = sorted([p.name for p in results])
        self.assertEqual(names, ["file1.txt", "file3.log"])

    def test_dedup_delete(self):
        duplicates = self.manager.dedup(self.root, delete=True, dry_run=False)
        self.assertEqual(len(duplicates), 1)
        # Check if the duplicate was deleted
        self.assertTrue(self.file1.exists() or self.file3.exists())
        self.assertFalse(self.file1.exists() and self.file3.exists())

    def test_usage(self):
        # We just test it doesn't crash
        self.manager.usage(self.root)

    def test_format_size(self):
        self.assertEqual(self.manager._format_size(500), "500.00 B")
        self.assertEqual(self.manager._format_size(2048), "2.00 KB")

    def test_parse_size(self):
        self.assertEqual(self.manager._parse_size("1K"), 1024)
        self.assertEqual(self.manager._parse_size("1KB"), 1024)
        self.assertEqual(self.manager._parse_size("1.5M"), int(1.5 * 1024 * 1024))

    def test_parse_time(self):
        self.assertEqual(self.manager._parse_time("1m"), 60)
        self.assertEqual(self.manager._parse_time("1h"), 3600)
        self.assertEqual(self.manager._parse_time("1d"), 86400)


@pytest.mark.asyncio
async def test_tui_fs_lab():
    pytest.importorskip("textual")
    from shared.tui import AgentTUI

    # Create a temporary directory and file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        from shared.database import init_db
        init_db(tmp_path / ".agent_db.sqlite")
        app = AgentTUI(project_dir=tmp_path, start_tab="tab-fs")

        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()

            # Navigate to the tab
            app.query_one("#main-tabs").active = "tab-fs"
            await pilot.pause()

            # Ensure fs lab tab is mounted
            fs_tab = app.query_one("#tab-fs")
            assert fs_tab is not None

            # Mock the selected path
            fs_tab = app.query_one("FsLabTab")
            fs_tab.selected_path = test_file
            fs_tab._update_selected_path()
            await pilot.pause()

            # Simulate directory selected
            fs_tab.selected_path = tmp_path
            fs_tab._update_selected_path()
            await pilot.pause()

            # Select file again
            fs_tab.selected_path = test_file
            fs_tab._update_selected_path()
            await pilot.pause()

            # Test Get Info button
            app.query_one("#btn-fs-info").press()
            await pilot.pause()

            # Verify log output contains file name
            from textual.widgets import RichLog
            log = app.query_one("#fs-info-log", RichLog)
            log_text = str(list(log.lines))
            assert "Info for test.txt" in log_text

            # Test Get Usage button
            app.query_one("#btn-fs-usage").press()
            await pilot.pause()

            # Test Find functionality
            # Set search term
            app.query_one("#fs-find-name").value = "*.txt"
            app.query_one("#fs-find-size").value = "<10M"
            app.query_one("#fs-find-mtime").value = "<1d"
            from textual.widgets import Select
            app.query_one("#fs-find-type", Select).value = "f"
            app.query_one("#fs-find-content").value = "hello"

            app.query_one("#btn-fs-find").press()
            await pilot.pause()

            log_text = str(list(log.lines))
            assert "Found" in log_text
            assert "test.txt" in log_text

            # Test Dedup functionality
            app.query_one("#btn-fs-dedup").press()
            await pilot.pause()
            log_text = str(list(log.lines))
            assert "Found" in log_text

            # Test Clean functionality
            app.query_one("#btn-fs-clean").press()
            await pilot.pause()
            log_text = str(list(log.lines))
            assert "Summary" in log_text

            # Test Shred functionality
            app.query_one("#btn-fs-shred").press()
            await pilot.pause()
            log_text = str(list(log.lines))
            assert "Successfully shredded" in log_text or "Failed to shred" in log_text

            # Test refresh
            app.query_one("#btn-fs-refresh-tree").press()
            await pilot.pause()
