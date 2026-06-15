import unittest
from unittest.mock import MagicMock, patch
import asyncio
from textual.widgets import Input, RichLog
from shared.tui_tree import TreeLabTab

class TestTreeLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.patcher = patch("shared.tui_tree.TreeLabManager")
        self.MockManager = self.patcher.start()

        self.tab = TreeLabTab()
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    @patch("shared.tui_tree.Path")
    async def test_generate_tree_success(self, MockPath):
        # Mock Inputs
        dir_input = MagicMock(spec=Input)
        dir_input.value = "/test/dir"
        depth_input = MagicMock(spec=Input)
        depth_input.value = "2"
        excludes_input = MagicMock(spec=Input)
        excludes_input.value = "node_modules, .git"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#input-tree-dir": return dir_input
            if selector == "#input-tree-depth": return depth_input
            if selector == "#input-tree-excludes": return excludes_input
            if selector == "#log-tree-output": return log
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        # Mock Path
        mock_path_instance = MockPath.return_value
        mock_path_instance.exists.return_value = True
        mock_path_instance.resolve.return_value.name = "dir"

        # Mock Manager Result
        mock_manager_instance = self.MockManager.return_value
        mock_manager_instance.generate_tree.return_value = "├── file.txt\n└── dir2"

        # Run
        await self.tab.generate_tree()

        # Verify manager instantiation args
        self.MockManager.assert_called_with(exclude=['node_modules', '.git'])

        # Verify manager call
        mock_manager_instance.generate_tree.assert_called_with(mock_path_instance, 2)

        # Verify UI updates
        log.clear.assert_called()
        log.write.assert_called()
        args, _ = log.write.call_args
        self.assertIn("dir/", args[0])
        self.assertIn("├── file.txt", args[0])
        self.tab.notify.assert_called_with("Tree generated successfully.")

    @patch("shared.tui_tree.Path")
    async def test_generate_tree_invalid_depth(self, MockPath):
        depth_input = MagicMock(spec=Input)
        depth_input.value = "invalid"

        def query_side_effect(selector, type=None):
            if selector == "#input-tree-dir": return MagicMock(value=".")
            if selector == "#input-tree-depth": return depth_input
            if selector == "#input-tree-excludes": return MagicMock(value="")
            if selector == "#log-tree-output": return MagicMock()
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        await self.tab.generate_tree()

        self.tab.notify.assert_called_with("Max depth must be an integer.", severity="error")

    @patch("shared.tui_tree.Path")
    async def test_generate_tree_non_existent_dir(self, MockPath):
        def query_side_effect(selector, type=None):
            if selector == "#input-tree-dir": return MagicMock(value="fake_dir")
            if selector == "#input-tree-depth": return MagicMock(value="-1")
            if selector == "#input-tree-excludes": return MagicMock(value="")
            if selector == "#log-tree-output": return MagicMock()
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        mock_path_instance = MockPath.return_value
        mock_path_instance.exists.return_value = False

        await self.tab.generate_tree()

        self.tab.notify.assert_called_with("Directory does not exist.", severity="error")

if __name__ == "__main__":
    unittest.main()
