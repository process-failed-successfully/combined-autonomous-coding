import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Input, RichLog, TextArea, Select, ListView, ListItem
from shared.tui import ScaffoldTab

class TestTUIScaffold(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock Manager
        self.patcher_manager = patch("shared.tui.ScaffoldManager")
        self.mock_manager_cls = self.patcher_manager.start()
        self.mock_manager = self.mock_manager_cls.return_value

    def tearDown(self):
        self.patcher_manager.stop()
        shutil.rmtree(self.test_dir)

    async def test_generate_preview(self):
        tab = ScaffoldTab(self.project_dir)
        tab.notify = MagicMock()

        # Mock widgets
        mock_desc = MagicMock(spec=TextArea)
        mock_desc.text = "My App"

        mock_select = MagicMock(spec=Select)
        mock_select.value = "gemini"

        mock_log = MagicMock(spec=RichLog)

        mock_btn = MagicMock() # Create button

        def query_side_effect(selector, type=None):
            sel_str = str(selector)
            if "description" in sel_str: return mock_desc
            if "agent" in sel_str: return mock_select
            if "log" in sel_str: return mock_log
            if "create" in sel_str: return mock_btn
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_side_effect)

        # Mock manager
        expected_plan = {"main.py": "code"}
        self.mock_manager.generate_ai_scaffold = AsyncMock(return_value=expected_plan)

        await tab.generate_preview()

        self.mock_manager.generate_ai_scaffold.assert_awaited_with("My App", agent_type="gemini")
        self.assertEqual(tab.ai_plan, expected_plan)
        mock_log.write.assert_called()

        # Verify create button enabled
        self.assertFalse(mock_btn.disabled)

    async def test_create_project_ai(self):
        tab = ScaffoldTab(self.project_dir)
        tab.notify = MagicMock()
        tab.ai_plan = {"main.py": "code"}

        # Mock List Selection
        mock_list = MagicMock(spec=ListView)
        mock_item = MagicMock(spec=ListItem)
        mock_item.template_name = "ai_custom"
        mock_list.index = 0
        mock_list.children = [mock_item]

        mock_log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            sel_str = str(selector)
            if "list" in sel_str: return mock_list
            if "log" in sel_str: return mock_log
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_side_effect)

        self.mock_manager.create_from_plan.return_value = True

        await tab.create_project()

        self.mock_manager.create_from_plan.assert_called_with(tab.ai_plan)
        # Should notify success
        tab.notify.assert_called_with("Project created successfully!", severity="information")
        mock_log.write.assert_called()

if __name__ == "__main__":
    unittest.main()
