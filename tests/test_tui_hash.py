import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.widgets import Input, RichLog, DataTable, TextArea, Select, Checkbox
from shared.tui_hash import HashLabTab

class TestHashLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.patcher = patch("shared.tui_hash.HashLabManager")
        self.MockManager = self.patcher.start()

        # We use a real Path for project_dir to avoid issues with / operator if spec doesn't handle it well,
        # but MagicMock(spec=Path) usually handles it if __truediv__ is mocked.
        # Simpler to use a MagicMock and trust standard mock behavior or just a real path if we don't care.
        # But sticking to Mock for isolation.
        self.project_dir = MagicMock(spec=Path)

        self.tab = HashLabTab(project_dir=self.project_dir)
        self.mock_manager = self.MockManager.return_value
        self.tab.manager = self.mock_manager

        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    def test_hash_string(self):
        # Mock Inputs
        text_input = MagicMock(spec=TextArea)
        text_input.text = "hello"
        algo_select = MagicMock(spec=Select)
        algo_select.value = "md5"
        hmac_input = MagicMock(spec=Input)
        hmac_input.value = "secret"
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#hash-string-input": return text_input
            if selector == "#hash-string-algo": return algo_select
            if selector == "#hash-string-hmac": return hmac_input
            if selector == "#hash-string-output": return output_area
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.hash_string.return_value = "hash123"

        # Run
        self.tab.hash_string()

        # Verify
        self.mock_manager.hash_string.assert_called_with("hello", "md5", "secret")
        self.assertEqual(output_area.text, "hash123")
        self.tab.notify.assert_called_with("Hash calculated.")

    async def test_hash_file(self):
        # Mock Inputs
        path_input = MagicMock(spec=Input)
        path_input.value = "test.txt"
        algo_select = MagicMock(spec=Select)
        algo_select.value = "sha1"
        hmac_input = MagicMock(spec=Input)
        hmac_input.value = None
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#hash-file-input": return path_input
            if selector == "#hash-file-algo": return algo_select
            if selector == "#hash-file-hmac": return hmac_input
            if selector == "#hash-file-output": return output_area
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.hash_file.return_value = "filehash123"

        # Run
        await self.tab.hash_file()

        # Verify
        self.mock_manager.hash_file.assert_called_with(self.project_dir / "test.txt", "sha1", None)
        self.assertEqual(output_area.text, "filehash123")
        self.tab.notify.assert_called_with("File hashed.")

    async def test_hash_dir(self):
        path_input = MagicMock(spec=Input)
        path_input.value = "src"
        algo_select = MagicMock(spec=Select)
        algo_select.value = "sha256"
        recursive_chk = MagicMock(spec=Checkbox)
        recursive_chk.value = True
        hmac_input = MagicMock(spec=Input)
        hmac_input.value = None
        table = MagicMock(spec=DataTable)

        def query_side_effect(selector, type=None):
            if selector == "#hash-dir-input": return path_input
            if selector == "#hash-dir-algo": return algo_select
            if selector == "#hash-dir-hmac": return hmac_input
            if selector == "#hash-dir-recursive": return recursive_chk
            if selector == "#hash-dir-table": return table
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.hash_dir.return_value = {"src/a.txt": "h1", "src/b.txt": "h2"}

        await self.tab.hash_dir()

        self.mock_manager.hash_dir.assert_called_with(self.project_dir / "src", "sha256", True, None)
        table.clear.assert_called()
        self.assertEqual(table.add_row.call_count, 2)
        # Notify msg depends on length of results
        self.tab.notify.assert_called_with("Hashed 2 files.")

    async def test_compare_files(self):
        p1 = MagicMock(spec=Input); p1.value = "a.txt"
        p2 = MagicMock(spec=Input); p2.value = "b.txt"
        algo = MagicMock(spec=Select); algo.value = "md5"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#hash-compare-1": return p1
            if selector == "#hash-compare-2": return p2
            if selector == "#hash-compare-algo": return algo
            if selector == "#hash-compare-log": return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.compare_files.return_value = {"match": True, "hash1": "h", "hash2": "h", "file1": "a", "file2": "b", "algo": "md5"}

        await self.tab.compare_files()

        self.mock_manager.compare_files.assert_called()
        log.write.assert_called()
        # verify success message
        call_args_list = log.write.call_args_list
        found_match = any("FILES MATCH" in str(c) for c in call_args_list)
        self.assertTrue(found_match)

    async def test_verify_checksums(self):
        sum_file = MagicMock(spec=Input); sum_file.value = "sums.txt"
        root = MagicMock(spec=Input); root.value = ""
        algo = MagicMock(spec=Select); algo.value = "sha256"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#hash-sum-file": return sum_file
            if selector == "#hash-sum-root": return root
            if selector == "#hash-sum-algo": return algo
            if selector == "#hash-sum-log": return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.verify_checksums.return_value = {
            "passed": ["a.txt"],
            "failed": [],
            "missing": [],
            "errors": []
        }

        await self.tab.verify_checksums()

        self.mock_manager.verify_checksums.assert_called()
        log.write.assert_called()
        found_pass = any("All checks passed" in str(c) for c in log.write.call_args_list)
        self.assertTrue(found_pass)

if __name__ == "__main__":
    unittest.main()
