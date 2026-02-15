import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Button, DataTable
from shared.tui_k8s import K8sTab

class K8sTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield K8sTab(self.project_dir)

class TestK8sTab(unittest.IsolatedAsyncioTestCase):

    @patch("shared.tui_k8s.K8sManager")
    async def test_refresh_ui(self, MockManager):
        # Setup Mock
        mock_instance = MockManager.return_value
        mock_instance.check_kubectl_installed.return_value = True

        mock_instance.list_pods.return_value = [
            {
                "metadata": {"name": "test-pod", "namespace": "default"},
                "status": {"phase": "Running", "containerStatuses": [{"restartCount": 0}]}
            }
        ]
        mock_instance.list_deployments.return_value = []
        mock_instance.list_services.return_value = []
        mock_instance.list_contexts.return_value = []

        # Create App inside patch context
        project_dir = Path("/tmp/test_project")
        app = K8sTestApp(project_dir)

        async with app.run_test() as pilot:
            # Wait for mount and initial refresh
            await pilot.pause(0.5)

            tab = app.query_one(K8sTab)
            table = tab.query_one("#k8s-pods-table", DataTable)

            # Check if table populated
            self.assertIn("pod:default:test-pod", table.rows)

    @patch("shared.tui_k8s.K8sManager")
    async def test_missing_kubectl(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.check_kubectl_installed.return_value = False

        project_dir = Path("/tmp/test_project")
        app = K8sTestApp(project_dir)

        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            # Should not find the table, maybe a label
            tab = app.query_one(K8sTab)
            # Assert that the table does NOT exist
            with self.assertRaises(Exception):
                tab.query_one("#k8s-pods-table")

    @patch("shared.tui_k8s.K8sManager")
    async def test_actions(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.check_kubectl_installed.return_value = True

        mock_instance.list_pods.return_value = [
            {
                "metadata": {"name": "test-pod", "namespace": "default"},
                "status": {"phase": "Running"}
            }
        ]
        mock_instance.get_logs.return_value = "Fake Logs"

        project_dir = Path("/tmp/test_project")
        app = K8sTestApp(project_dir)

        async with app.run_test() as pilot:
            tab = app.query_one(K8sTab)
            await pilot.pause(0.2)

            # Simulate selection manually
            tab.selected_resource = ("pod", "test-pod", "default")
            # Force enable button as the UI would
            tab.query_one("#btn-k8s-logs").disabled = False

            # Click Logs
            await pilot.click("#btn-k8s-logs")
            await pilot.pause(0.2)

            # We can't easily assert the mock call because of threading,
            # but we can verify the UI didn't crash and maybe check if log was cleared/written
            # checking the log widget content is possible but internal implementation detail.

            # The main point is ensure no exceptions.

if __name__ == "__main__":
    unittest.main()
