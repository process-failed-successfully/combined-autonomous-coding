import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.cicd_lab import CicdLabManager

class TestCicdLabManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

        # Patch config loader to avoid file system reads and ensure token
        self.config_patcher = patch('shared.cicd_lab.load_config_from_file')
        self.mock_load_config = self.config_patcher.start()
        self.mock_load_config.return_value = {"github_token": "test_token"}

        # Patch GitHubClient to avoid network calls
        self.client_patcher = patch('shared.cicd_lab.GitHubClient')
        self.mock_client_class = self.client_patcher.start()
        self.mock_client = self.mock_client_class.return_value

        self.manager = CicdLabManager(self.project_dir)

    def tearDown(self):
        self.config_patcher.stop()
        self.client_patcher.stop()

    def test_list_workflows_success(self):
        self.mock_client.list_workflows.return_value = {"workflows": [{"id": 1, "name": "CI"}]}
        workflows = self.manager.list_workflows()
        self.assertEqual(len(workflows), 1)
        self.assertEqual(workflows[0]["name"], "CI")
        self.mock_client.list_workflows.assert_called_once_with(self.project_dir)

    def test_list_workflows_error(self):
        self.mock_client.list_workflows.side_effect = Exception("API Error")
        workflows = self.manager.list_workflows()
        self.assertEqual(len(workflows), 1)
        self.assertIn("error", workflows[0])

    def test_list_runs(self):
        self.mock_client.list_workflow_runs.return_value = {"workflow_runs": [{"id": 123, "status": "completed"}]}
        runs = self.manager.list_runs(1)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["id"], 123)
        self.mock_client.list_workflow_runs.assert_called_once_with(self.project_dir, 1, per_page=20)

    def test_trigger_workflow(self):
        self.mock_client.trigger_workflow_dispatch.return_value = True
        result = self.manager.trigger_workflow(1, "main", {"key": "value"})
        self.assertTrue(result)
        self.mock_client.trigger_workflow_dispatch.assert_called_once_with(self.project_dir, 1, "main", {"key": "value"})

    def test_get_workflow_inputs(self):
        # Create a temporary workflow file
        import tempfile
        import shutil

        test_dir = Path(tempfile.mkdtemp())
        self.manager.project_dir = test_dir

        wf_dir = test_dir / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        wf_file = wf_dir / "test.yml"

        wf_content = """
name: Manual Trigger
on:
  workflow_dispatch:
    inputs:
      logLevel:
        description: 'Log level'
        required: true
        default: 'warning'
"""
        wf_file.write_text(wf_content)

        inputs = self.manager.get_workflow_inputs(".github/workflows/test.yml")
        self.assertIn("logLevel", inputs)

        shutil.rmtree(test_dir)

if __name__ == '__main__':
    unittest.main()
