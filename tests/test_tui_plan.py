import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.widgets import TextArea, Label
from textual.app import App, ComposeResult

# We need to import PlanTab. Since it's inside shared/tui.py which has other deps,
# we rely on the installed deps.
from shared.tui import PlanTab

class TestPlanTab(unittest.IsolatedAsyncioTestCase):
    async def test_plan_tab_initialization(self):
        project_dir = Path("./test_project_tui")
        project_dir.mkdir(exist_ok=True)
        (project_dir / "app_spec.txt").write_text("Spec Content")
        (project_dir / "feature_list.json").write_text('{"features": []}')

        try:
            tab = PlanTab(project_dir)
            # Mount the widget in a headless app to trigger on_mount
            app = App()
            async with app.run_test() as pilot:
                await pilot.app.mount(tab)

                # Check if spec loaded
                editor = tab.query_one("#spec-editor", TextArea)
                self.assertEqual(editor.text, "Spec Content")

                # Check if plan loaded
                viewer = tab.query_one("#plan-viewer", TextArea)
                self.assertEqual(viewer.text, '{"features": []}')
        finally:
            import shutil
            if project_dir.exists():
                shutil.rmtree(project_dir)

    @patch("shared.tui.run_plan_logic")
    async def test_generate_plan_interaction(self, mock_run_plan):
        # Setup mock
        mock_run_plan.return_value = (True, "Success")

        project_dir = Path("./test_project_tui_gen")
        project_dir.mkdir(exist_ok=True)
        (project_dir / "app_spec.txt").write_text("Spec Content")

        try:
            tab = PlanTab(project_dir)
            app = App()
            async with app.run_test() as pilot:
                await pilot.app.mount(tab)

                # Modify spec
                editor = tab.query_one("#spec-editor", TextArea)
                editor.load_text("Updated Spec")
                await pilot.pause()

                # Click generate
                await pilot.click("#btn-generate-plan")
                await pilot.pause()

                # Verify save was called (file updated)
                self.assertEqual((project_dir / "app_spec.txt").read_text(), "Updated Spec")

                # Verify run_plan_logic called
                mock_run_plan.assert_called_once()
                args = mock_run_plan.call_args
                self.assertEqual(args.kwargs['agent_type'], "gemini") # default

        finally:
            import shutil
            if project_dir.exists():
                shutil.rmtree(project_dir)

if __name__ == "__main__":
    unittest.main()
