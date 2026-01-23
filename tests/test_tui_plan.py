import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile
import json

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Button, DataTable, Input, TextArea
from shared.tui import PlanTab

class TestPlanTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()
        self.feature_file = self.project_dir / "feature_list.json"
        self.spec_file = self.project_dir / "app_spec.txt"

        # Mock run_plan_logic
        self.patcher_plan = patch("shared.tui.run_plan_logic", new_callable=AsyncMock)
        self.mock_run_plan = self.patcher_plan.start()
        self.mock_run_plan.return_value = True

    def tearDown(self):
        self.patcher_plan.stop()
        shutil.rmtree(self.test_dir)

    async def test_compose_and_load(self):
        """Test tab composition and initial load."""
        # Setup initial files
        self.spec_file.write_text("Build a cool app.")
        self.feature_file.write_text(json.dumps([
            {"name": "Login", "status": "completed", "description": "User login"}
        ]))

        tab = PlanTab(self.project_dir)

        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(160, 80)) as pilot:
            # Check widgets exist
            self.assertIsNotNone(app.query_one("#spec-editor", TextArea))
            self.assertIsNotNone(app.query_one("#features-table", DataTable))
            self.assertIsNotNone(app.query_one("#btn-save-spec", Button))
            self.assertIsNotNone(app.query_one("#btn-generate-plan", Button))

            # Check Spec loaded
            spec_editor = app.query_one("#spec-editor", TextArea)
            self.assertEqual(spec_editor.text, "Build a cool app.")

            # Check Features loaded
            table = app.query_one("#features-table", DataTable)
            self.assertEqual(table.row_count, 1)
            # Textual tables are complex to query cells directly, but row count is good enough

    async def test_generate_plan(self):
        """Test the generate plan button."""
        tab = PlanTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(160, 80)) as pilot:
            # Click Generate
            await pilot.click("#btn-generate-plan")

            # Verify logic called
            self.mock_run_plan.assert_called_with(
                self.project_dir,
                spec_file=self.spec_file,
                agent_type="gemini"
            )

    async def test_add_feature(self):
        """Test adding a feature manually."""
        tab = PlanTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(320, 80)) as pilot:
            inp = app.query_one("#feature-name-input", Input)
            inp.value = "New Feature"

            app.set_focus(app.query_one("#btn-add-feature"))
            await pilot.press("enter")

            # Check file updated
            features = json.loads(self.feature_file.read_text())
            self.assertEqual(len(features), 1)
            self.assertEqual(features[0]["name"], "New Feature")

    async def test_save_spec(self):
        """Test saving the spec."""
        tab = PlanTab(self.project_dir)
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test(size=(160, 80)) as pilot:
            editor = app.query_one("#spec-editor", TextArea)
            editor.text = "Updated Spec"

            await pilot.click("#btn-save-spec")

            # Check file updated
            self.assertEqual(self.spec_file.read_text(), "Updated Spec")

if __name__ == "__main__":
    unittest.main()
