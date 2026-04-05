import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, ListView, Checkbox, Markdown, Select
from shared.tui import CodeReviewTab

class TestCodeReviewTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Patch run_code_review_logic
        self.patcher_logic = patch("shared.tui.run_code_review_logic", new_callable=AsyncMock)
        self.mock_logic = self.patcher_logic.start()
        # It needs to return True/False
        self.mock_logic.return_value = True

        # Patch subprocess for load_files
        self.patcher_subprocess = patch("subprocess.run")
        self.mock_subprocess = self.patcher_subprocess.start()

        # Default git status output
        self.mock_result = MagicMock()
        self.mock_result.returncode = 0
        self.mock_result.stdout = "M  file1.py\n?? new_file.py"
        self.mock_subprocess.return_value = self.mock_result

    def tearDown(self):
        self.patcher_logic.stop()
        self.patcher_subprocess.stop()
        shutil.rmtree(self.test_dir)

    async def test_compose_and_load(self):
        """Test tab composition and initial file loading."""
        tab = CodeReviewTab(self.project_dir)

        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # Check widgets exist
            self.assertIsNotNone(app.query_one("#review-file-list"))
            self.assertIsNotNone(app.query_one("#btn-review-refresh"))
            self.assertIsNotNone(app.query_one("#btn-review-selected"))
            self.assertIsNotNone(app.query_one("#btn-review-all"))
            self.assertIsNotNone(app.query_one("#review-markdown"))

            # Verify subprocess call
            self.mock_subprocess.assert_called()

            # Check list items
            list_view = app.query_one("#review-file-list", ListView)
            self.assertEqual(len(list_view.children), 2)

            # Verify checkboxes content
            # Accessing label of Checkbox. Textual Checkbox label is a property.
            cb1 = list_view.children[0].query_one(Checkbox)
            self.assertIn("file1.py", str(cb1.label))
            self.assertTrue(cb1.value)

    async def test_review_selected(self):
        """Test 'Review Selected' button."""
        tab = CodeReviewTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # Ensure files are loaded (on_mount)
            # The list should have file1.py and new_file.py selected by default

            # Click Review Selected
            pilot.app.query_one("#btn-review-selected").press()
            await pilot.pause()

            # Verify logic call
            self.mock_logic.assert_called_once()
            call_args = self.mock_logic.call_args
            # kwargs check
            kwargs = call_args.kwargs
            self.assertEqual(kwargs['project_dir'], self.project_dir)
            self.assertEqual(kwargs['agent_type'], "gemini") # default
            self.assertFalse(kwargs['diff'])
            self.assertIn("file1.py", kwargs['files'])
            self.assertIn("new_file.py", kwargs['files'])

    async def test_review_all(self):
        """Test 'Review All' button."""
        tab = CodeReviewTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # Click Review All
            pilot.app.query_one("#btn-review-all").press()
            await pilot.pause()

            # Verify logic call
            self.mock_logic.assert_called_once()
            call_args = self.mock_logic.call_args
            kwargs = call_args.kwargs
            self.assertTrue(kwargs['diff'])
            self.assertIsNone(kwargs['files'])

    async def test_refresh(self):
        """Test Refresh button."""
        tab = CodeReviewTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # Initial load count
            initial_count = self.mock_subprocess.call_count

            # Click Refresh
            pilot.app.query_one("#btn-review-refresh").press()
            await pilot.pause()

            # Verify called again
            # Note: call_count increases by 1
            self.assertEqual(self.mock_subprocess.call_count, initial_count + 1)

if __name__ == "__main__":
    unittest.main()
