import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Input, DataTable, Markdown, Select  # noqa: E402
from shared.tui import TroubleshootTab  # noqa: E402


class TestTUITroubleshoot(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock TroubleshootManager
        self.patcher_manager = patch("shared.tui.TroubleshootManager")
        self.mock_manager_cls = self.patcher_manager.start()
        self.mock_manager = self.mock_manager_cls.return_value

    def tearDown(self):
        self.patcher_manager.stop()
        shutil.rmtree(self.test_dir)

    async def test_compose(self):
        """Test the UI composition."""
        tab = TroubleshootTab(self.project_dir)
        self.assertIsNotNone(tab)

    async def test_run_analysis(self):
        """Test the analysis logic."""
        tab = TroubleshootTab(self.project_dir)
        tab.notify = MagicMock()

        mock_table = MagicMock(spec=DataTable)
        # Mocking query_one to return the DataTable when requested
        tab.query_one = MagicMock(side_effect=lambda selector, type=None: mock_table if "table" in str(selector) else MagicMock())

        # Mock detect_issues return value
        self.mock_manager.detect_issues.return_value = {
            "lint": {"success": False, "stderr": "Lint error"}
        }

        await tab.run_analysis()

        self.mock_manager.detect_issues.assert_called_once()
        mock_table.clear.assert_called()
        mock_table.add_row.assert_called()
        # Verify "FAILED" status was added
        args, _ = mock_table.add_row.call_args
        self.assertIn("LINT", args[0])
        self.assertIn("[red]FAILED[/red]", args[1])

    async def test_run_diagnosis(self):
        """Test diagnosis logic."""
        tab = TroubleshootTab(self.project_dir)
        tab.notify = MagicMock()
        tab.issues = {"lint": {"success": False}}  # Pre-populate issues

        mock_input = MagicMock(spec=Input)
        mock_input.value = "Fix lint"

        mock_select = MagicMock(spec=Select)
        mock_select.value = "gemini"

        mock_md = MagicMock(spec=Markdown)

        # Mock query_one to return specific widgets based on selector
        def query_side_effect(selector, type=None):
            sel_str = str(selector)
            if "issue" in sel_str:
                return mock_input
            if "agent" in sel_str:
                return mock_select
            if "markdown" in sel_str:
                return mock_md
            return MagicMock()  # Fallback for buttons

        tab.query_one = MagicMock(side_effect=query_side_effect)

        self.mock_manager.diagnose = AsyncMock(return_value="Diagnosis Plan")

        await tab.run_diagnosis()

        # Should re-init manager (mock_manager_cls called)
        self.mock_manager_cls.assert_called_with(self.project_dir, agent_type="gemini")
        # Should call diagnose on the NEW manager instance returned by constructor
        # Since we mocked the class return value, self.mock_manager refers to that instance
        self.mock_manager.diagnose.assert_awaited_with(tab.issues, user_query="Fix lint")
        mock_md.update.assert_called_with("Diagnosis Plan")

    async def test_run_fix(self):
        """Test apply fix logic."""
        tab = TroubleshootTab(self.project_dir)
        tab.notify = MagicMock()

        mock_md = MagicMock(spec=Markdown)
        tab.query_one = MagicMock(return_value=mock_md)

        self.mock_manager.apply_fix = AsyncMock(return_value="Fix applied successfully")

        await tab.run_fix()

        self.mock_manager.apply_fix.assert_awaited()
        # Verify markdown update contains success message
        mock_md.update.assert_called()
        args, _ = mock_md.update.call_args
        self.assertIn("Fix applied successfully", args[0])


if __name__ == "__main__":
    unittest.main()
