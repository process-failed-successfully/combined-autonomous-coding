import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Button, Select, TextArea  # noqa: E402
from shared.tui import TestGenTab  # noqa: E402


class TestTUITestGen(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    async def test_tab_structure(self):
        tab = TestGenTab(self.project_dir)
        self.assertIsNotNone(tab)

    async def test_file_selection(self):
        tab = TestGenTab(self.project_dir)
        tab.notify = MagicMock()

        mock_btn = MagicMock(spec=Button)
        tab.query_one = MagicMock(return_value=mock_btn)

        # Create a dummy event
        event = MagicMock()
        event.path = self.project_dir / "file.py"
        # Make path look like a file
        with patch('pathlib.Path.is_file', return_value=True):
            tab.on_directory_tree_file_selected(event)

        self.assertEqual(tab.selected_file, event.path)
        self.assertEqual(mock_btn.disabled, False)

    @patch('shared.tui.TestGenTab.query_one')
    @patch('shared.test_generator.TestGenerator')
    async def test_generate_tests_success(self, mock_generator_cls, mock_query_one):
        tab = TestGenTab(self.project_dir)
        tab.selected_file = self.project_dir / "file.py"
        tab.notify = MagicMock()

        # Mock widgets
        mock_framework = MagicMock(spec=Select)
        mock_framework.value = "pytest"
        mock_agent = MagicMock(spec=Select)
        mock_agent.value = "gemini"
        mock_preview = MagicMock(spec=TextArea)
        mock_save_btn = MagicMock(spec=Button)

        def query_side_effect(selector, *args, **kwargs):
            if "#testgen-framework" in selector:
                return mock_framework
            if "#testgen-agent" in selector:
                return mock_agent
            if "#testgen-preview" in selector:
                return mock_preview
            if "#btn-testgen-save" in selector:
                return mock_save_btn
            return MagicMock()

        mock_query_one.side_effect = query_side_effect

        # Mock generator
        mock_gen_instance = mock_generator_cls.return_value
        mock_gen_instance.generate_test_code = AsyncMock(return_value=(True, "def test_foo(): pass"))

        await tab.generate_tests()

        mock_gen_instance.generate_test_code.assert_awaited_once()
        self.assertEqual(mock_preview.text, "def test_foo(): pass")
        self.assertEqual(mock_save_btn.disabled, False)

    @patch('shared.tui.TestGenTab.query_one')
    async def test_save_tests(self, mock_query_one):
        tab = TestGenTab(self.project_dir)
        tab.selected_file = self.project_dir / "file.py"
        tab.notify = MagicMock()

        mock_preview = MagicMock(spec=TextArea)
        mock_preview.text = "def test_foo(): pass"

        mock_query_one.return_value = mock_preview

        await tab.save_tests()

        expected_path = self.project_dir / "tests" / "test_file.py"
        self.assertTrue(expected_path.exists())
        self.assertEqual(expected_path.read_text(encoding="utf-8"), "def test_foo(): pass")


if __name__ == "__main__":
    unittest.main()
