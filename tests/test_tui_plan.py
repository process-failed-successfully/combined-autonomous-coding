import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, TextArea
from shared.tui import PlanTab

class TestPlanTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Patch run_plan_logic
        self.patcher_logic = patch("shared.tui.run_plan_logic", new_callable=AsyncMock)
        self.mock_run_plan_logic = self.patcher_logic.start()
        self.mock_run_plan_logic.return_value = (True, "Mock Plan Generated")

    def tearDown(self):
        self.patcher_logic.stop()
        shutil.rmtree(self.test_dir)

    async def test_compose_and_load(self):
        """Test tab composition and initial load."""
        tab = PlanTab(self.project_dir)

        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(120, 40)) as pilot:
            # Check widgets exist
            self.assertIsNotNone(app.query_one("#spec-editor"))
            self.assertIsNotNone(app.query_one("#plan-editor"))
            self.assertIsNotNone(app.query_one("#btn-generate-plan"))

            # Check default text
            spec = app.query_one("#spec-editor", TextArea)
            self.assertIn("Application Specification", spec.text)

    async def test_save_spec(self):
        """Test saving the spec file."""
        tab = PlanTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(120, 40)) as pilot:
            spec_editor = app.query_one("#spec-editor", TextArea)
            spec_editor.text = "New Spec Content"

            pilot.app.query_one("#btn-save-spec").press()
            await pilot.pause()

            spec_path = self.project_dir / "app_spec.txt"
            self.assertTrue(spec_path.exists())
            self.assertEqual(spec_path.read_text(encoding="utf-8"), "New Spec Content")

    async def test_save_plan(self):
        """Test saving the plan file."""
        tab = PlanTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(120, 40)) as pilot:
            plan_editor = app.query_one("#plan-editor", TextArea)
            plan_editor.text = '{"tasks": []}'

            pilot.app.query_one("#btn-save-plan").press()
            await pilot.pause()

            plan_path = self.project_dir / "feature_list.json"
            self.assertTrue(plan_path.exists())
            self.assertEqual(plan_path.read_text(encoding="utf-8"), '{"tasks": []}')

    async def test_generate_plan(self):
        """Test generating the plan."""
        tab = PlanTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(120, 40)) as pilot:
            # Click generate
            pilot.app.query_one("#btn-generate-plan").press()
            await pilot.pause()

            # Verify logic call
            self.mock_run_plan_logic.assert_called_with(
                self.project_dir,
                agent_type="gemini", # Default
                capture_output=True
            )

if __name__ == "__main__":
    unittest.main()
