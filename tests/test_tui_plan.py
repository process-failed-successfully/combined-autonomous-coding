import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import TextArea, Button
from shared.tui import AgentTUI, PlanTab

class TestTUIPlan(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Create dummy files
        (self.project_dir / "app_spec.txt").write_text("Test Spec")
        (self.project_dir / "feature_list.json").write_text('[]')

        # Mock init_db to prevent side effects
        self.patcher_db = patch("shared.tui.init_db")
        self.mock_init_db = self.patcher_db.start()

    def tearDown(self):
        self.patcher_db.stop()
        shutil.rmtree(self.test_dir)

    async def test_plan_tab_structure(self):
        """Test the PlanTab structure and widget presence."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            # Switch to plan tab
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-plan"
            await pilot.pause()

            plan_tab = app.query_one(PlanTab)
            self.assertIsNotNone(plan_tab)

            # Check for editors
            spec_editor = plan_tab.query_one("#spec-editor", TextArea)
            plan_editor = plan_tab.query_one("#plan-editor", TextArea)
            self.assertIsNotNone(spec_editor)
            self.assertIsNotNone(plan_editor)

            # Check content loaded
            self.assertEqual(spec_editor.text, "Test Spec")
            self.assertIn("[]", plan_editor.text)

            # Check buttons
            self.assertTrue(plan_tab.query_one("#btn-save-spec", Button))
            self.assertTrue(plan_tab.query_one("#btn-save-plan", Button))
            self.assertTrue(plan_tab.query_one("#btn-generate-plan", Button))

    @patch("shared.tui.run_plan_logic", new_callable=AsyncMock)
    async def test_generate_plan_action(self, mock_run_plan):
        """Test the generate plan button action."""
        mock_run_plan.return_value = (True, "[]")

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-plan"
            await pilot.pause()

            # Click Generate Button
            await pilot.click("#btn-generate-plan")

            # Allow async event to process
            await pilot.pause()

            # Check if logic was called
            mock_run_plan.assert_called_once()

            # Check args
            call_args = mock_run_plan.call_args[1]
            self.assertEqual(call_args["project_dir"], self.project_dir)
            self.assertEqual(str(call_args["spec_file"]), str(self.project_dir / "app_spec.txt"))
            self.assertEqual(call_args["capture_output"], True)

    async def test_save_spec_action(self):
        """Test saving spec file."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            tabbed_content = app.query_one("#main-tabs")
            tabbed_content.active = "tab-plan"
            await pilot.pause()

            spec_editor = app.query_one("#spec-editor", TextArea)
            spec_editor.text = "Updated Spec Content"

            await pilot.click("#btn-save-spec")
            await pilot.pause()

            # Verify file written
            saved_content = (self.project_dir / "app_spec.txt").read_text()
            self.assertEqual(saved_content, "Updated Spec Content")

if __name__ == "__main__":
    unittest.main()
