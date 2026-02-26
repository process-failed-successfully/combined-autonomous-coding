import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.widgets import Button, ListView, DataTable, Input
from shared.tui_cicd import CicdLabTab

class TestCicdLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch CicdLabManager
        self.manager_patcher = patch('shared.tui_cicd.CicdLabManager')
        self.mock_manager_class = self.manager_patcher.start()
        self.mock_manager = self.mock_manager_class.return_value

        # Setup mock returns
        self.mock_manager.list_workflows.return_value = [{"id": 1, "name": "CI", "state": "active", "path": ".github/workflows/ci.yml"}]
        self.mock_manager.list_runs.return_value = [{"id": 101, "status": "completed", "conclusion": "success", "head_branch": "main", "head_sha": "abcdef1"}]
        self.mock_manager.get_run_jobs.return_value = [{"name": "build", "status": "completed", "conclusion": "success", "steps": []}]
        self.mock_manager.trigger_workflow.return_value = True

    def tearDown(self):
        self.manager_patcher.stop()

    async def test_load_workflows(self):
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield CicdLabTab(Path("/mock/project"))

        app = TestApp()
        async with app.run_test() as pilot:
            # Wait for async load to complete
            await pilot.pause()

            tab = app.query_one(CicdLabTab)
            # Workflows should load on mount
            list_view = tab.query_one("#cicd-workflow-list", ListView)
            self.assertEqual(len(list_view.children), 1)
            self.assertIn("CI", str(list_view.children[0].query_one("Label").renderable))

    async def test_trigger_workflow(self):
        from textual.app import App
        class TestApp(App):
            def compose(self):
                yield CicdLabTab(Path("/mock/project"))

        app = TestApp()
        async with app.run_test() as pilot:
            # Wait for initial load
            await pilot.pause()

            tab = app.query_one(CicdLabTab)

            # Select workflow
            list_view = tab.query_one("#cicd-workflow-list", ListView)
            list_view.index = 0
            list_view.post_message(ListView.Selected(list_view, list_view.children[0]))

            await pilot.pause()

            # Check trigger button enabled
            btn = tab.query_one("#btn-cicd-trigger", Button)
            self.assertFalse(btn.disabled)

            # Click trigger
            await pilot.click("#btn-cicd-trigger")

            # Wait for async task
            await pilot.pause()

            # Verify call
            self.mock_manager.trigger_workflow.assert_called()

if __name__ == '__main__':
    unittest.main()
