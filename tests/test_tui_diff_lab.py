import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys

class TestTuiDiffLab(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # Create a mock for textual
        mock_textual = MagicMock()
        mock_containers = MagicMock()
        # Ensure Container is a class that can be inherited from
        # We define a dummy class for Container
        class MockContainer:
            def __init__(self, *args, **kwargs):
                pass

        mock_containers.Container = MockContainer

        cls.patcher = patch.dict('sys.modules', {
            'textual': mock_textual,
            'textual.app': MagicMock(),
            'textual.widgets': MagicMock(),
            'textual.containers': mock_containers,
            'textual.binding': MagicMock(),
            'textual.reactive': MagicMock(),
            'textual.screen': MagicMock(),
            'rich.syntax': MagicMock(),
            # Mock DiffLabManager to avoid rich console issues
            'shared.diff_lab': MagicMock(),
        })
        cls.patcher.start()

        # Import after patching
        global DiffLabTab
        from shared.tui_diff_lab import DiffLabTab

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def setUp(self):
        self.project_dir = Path("/tmp")
        self.tab = DiffLabTab(self.project_dir)

        # Explicitly overwrite manager with a MagicMock to ensure tests work
        # regardless of import state
        self.tab.manager = MagicMock()

        self.tab.query_one = MagicMock()
        self.tab.notify = MagicMock()

    async def test_load_file_success(self):
        # Setup mocks
        input_mock = MagicMock()
        input_mock.value = "test.txt"
        textarea_mock = MagicMock()

        def query_side_effect(selector, *args):
            if "input-diff-path" in selector:
                return input_mock
            if "text-diff" in selector:
                return textarea_mock
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        with patch('pathlib.Path.exists', return_value=True), \
             patch('asyncio.to_thread', new_callable=AsyncMock) as mock_thread:

            mock_thread.return_value = "content"
            await self.tab.load_file("a")

        self.assertEqual(textarea_mock.text, "content")
        self.tab.notify.assert_called_with("Loaded test.txt")

    def test_compare_text(self):
        textarea_mock = MagicMock()
        textarea_mock.text = "content"
        select_mock = MagicMock()
        select_mock.value = "Text"
        log_mock = MagicMock()
        table_mock = MagicMock()

        def query_side_effect(selector, *args):
            if "text-diff" in selector:
                return textarea_mock
            if "select-diff-mode" in selector:
                return select_mock
            if "diff-result-log" in selector:
                return log_mock
            if "diff-result-table" in selector:
                return table_mock
            return MagicMock() # TabbedContent

        self.tab.query_one.side_effect = query_side_effect
        self.tab.manager.get_text_diff.return_value = ["diff lines"]

        self.tab.compare()

        self.tab.manager.get_text_diff.assert_called()
        log_mock.write.assert_called()

    def test_compare_json(self):
        # Setup mocks
        textarea_a = MagicMock()
        textarea_a.text = '{"a": 1}'
        textarea_b = MagicMock()
        textarea_b.text = '{"a": 2}'

        select_mock = MagicMock()
        select_mock.value = "JSON"
        log_mock = MagicMock()
        table_mock = MagicMock()

        def query_side_effect(selector, *args):
            if "text-diff-a" in selector:
                return textarea_a
            if "text-diff-b" in selector:
                return textarea_b
            if "select-diff-mode" in selector:
                return select_mock
            if "diff-result-log" in selector:
                return log_mock
            if "diff-result-table" in selector:
                return table_mock
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect
        self.tab.manager.get_structure_diff.return_value = [{"type": "MODIFIED", "path": "[a]", "old": 1, "new": 2}]

        self.tab.compare()

        # Debug if failed
        if not self.tab.manager.get_structure_diff.called:
             # Check if log.write called (parsing error)
             if log_mock.write.called:
                 print(f"Log error: {log_mock.write.call_args}")

        self.tab.manager.get_structure_diff.assert_called()
        table_mock.add_row.assert_called()

if __name__ == "__main__":
    unittest.main()
