import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import shutil
import tempfile

from textual.widgets import Input, DataTable, Markdown, Button, Select
from shared.tui import ProfileTab


class TestTUIProfile(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Create a dummy script to profile
        self.script_path = self.project_dir / "slow_script.py"
        self.script_path.write_text("import time\ndef slow():\n    time.sleep(0.1)\nslow()")

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    @patch("shared.tui.OptimizationManager")
    async def test_profile_tab_structure(self, MockOptimizationManager: MagicMock) -> None:
        """Test that the profile tab has the correct widgets."""
        tab = ProfileTab(self.project_dir)

        # We need to simulate the app structure for query_one to work if we were running full app test
        # But for unit testing the tab logic, we can inspect compose() or mocks.
        # Textual unit testing usually involves running the app.

        # Let's mock query_one
        mock_input_script = MagicMock(spec=Input)
        mock_input_args = MagicMock(spec=Input)
        mock_table = MagicMock(spec=DataTable)
        mock_markdown = MagicMock(spec=Markdown)
        mock_btn_analyze = MagicMock(spec=Button)

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {  # type: ignore
            "#profile-script-input": mock_input_script,
            "#profile-args-input": mock_input_args,
            "#profile-table": mock_table,
            "#profile-ai-output": mock_markdown,
            "#btn-analyze-profile": mock_btn_analyze,
            "#profile-agent-select": MagicMock(spec=Select)
        }.get(selector))

        # Initialize
        tab.on_mount()

        # Check table setup
        mock_table.add_columns.assert_called_with("Function", "File:Line", "Calls", "Total Time", "Cum Time")

    @patch("shared.tui.OptimizationManager")
    async def test_run_profile(self, MockOptimizationManager: MagicMock) -> None:
        """Test the run_profiler logic."""
        mock_manager = MockOptimizationManager.return_value
        mock_manager.run_profile.return_value = Path("stats_file")
        mock_manager.analyze_stats.return_value = [
            {"name": "slow", "filename": "slow_script.py", "line": 2, "ncalls": 1, "tottime": 0.1, "cumtime": 0.1}
        ]

        tab = ProfileTab(self.project_dir)

        # Mock UI
        mock_input_script = MagicMock(spec=Input)
        mock_input_script.value = "slow_script.py"
        mock_input_args = MagicMock(spec=Input)
        mock_input_args.value = ""
        mock_table = MagicMock(spec=DataTable)
        mock_btn_analyze = MagicMock(spec=Button)

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {  # type: ignore
            "#profile-script-input": mock_input_script,
            "#profile-args-input": mock_input_args,
            "#profile-table": mock_table,
            "#btn-analyze-profile": mock_btn_analyze
        }.get(selector))
        tab.notify = MagicMock()  # type: ignore

        # Run
        await tab.run_profiler()  # type: ignore

        # Verify calls
        mock_manager.run_profile.assert_called_with(self.project_dir / "slow_script.py", [])
        mock_manager.analyze_stats.assert_called()
        mock_table.add_row.assert_called()
        self.assertEqual(mock_btn_analyze.disabled, False)

    @patch("shared.tui.OptimizationManager")
    async def test_analyze_profile(self, MockOptimizationManager: MagicMock) -> None:
        """Test the analyze_profile logic."""
        mock_manager = MockOptimizationManager.return_value
        mock_manager.get_ai_suggestions = AsyncMock(return_value="AI Suggestion")

        tab = ProfileTab(self.project_dir)
        tab.stats_file = Path("stats_file")

        # Mock UI
        mock_select = MagicMock(spec=Select)
        mock_select.value = "gemini"
        mock_markdown = MagicMock(spec=Markdown)

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {  # type: ignore
            "#profile-agent-select": mock_select,
            "#profile-ai-output": mock_markdown
        }.get(selector))
        tab.notify = MagicMock()  # type: ignore

        # Run
        await tab.analyze_profile()  # type: ignore

        # Verify calls
        mock_manager.get_ai_suggestions.assert_called_with(Path("stats_file"), agent_type="gemini")
        mock_markdown.update.assert_called_with("AI Suggestion")


if __name__ == "__main__":
    unittest.main()
