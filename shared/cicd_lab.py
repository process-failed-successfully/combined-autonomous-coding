import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.github_client import GitHubClient
from shared.config_loader import load_config_from_file

class CicdLabManager:
    """Manages CI/CD operations via GitHub Actions."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config = load_config_from_file()
        token = os.environ.get("GITHUB_TOKEN") or self.config.get("github_token")
        host = self.config.get("github_host", "github.com")

        if not token:
            # We can't really function without a token, but let's allow init and fail on methods
            self.client = None
        else:
            self.client = GitHubClient(token=token, host=host)

    def _check_client(self):
        if not self.client:
            raise ValueError("GitHub token not found. Please set GITHUB_TOKEN environment variable or configure 'github_token' in agent_config.yaml.")

    def list_workflows(self) -> List[Dict[str, Any]]:
        """Lists all GitHub Actions workflows."""
        self._check_client()
        try:
            data = self.client.list_workflows(self.project_dir)
            return data.get("workflows", [])
        except Exception as e:
            return [{"error": str(e)}]

    def list_runs(self, workflow_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Lists runs for a specific workflow."""
        self._check_client()
        try:
            data = self.client.list_workflow_runs(self.project_dir, workflow_id, per_page=limit)
            return data.get("workflow_runs", [])
        except Exception as e:
            return [{"error": str(e)}]

    def get_run_jobs(self, run_id: int) -> List[Dict[str, Any]]:
        """Gets jobs for a specific run."""
        self._check_client()
        try:
            data = self.client.get_workflow_run_jobs(self.project_dir, run_id)
            return data.get("jobs", [])
        except Exception as e:
            return [{"error": str(e)}]

    def trigger_workflow(self, workflow_id: int, ref: str, inputs: Dict[str, str] = None) -> bool:
        """Triggers a workflow dispatch."""
        self._check_client()
        return self.client.trigger_workflow_dispatch(self.project_dir, workflow_id, ref, inputs)

    def get_workflow_inputs(self, workflow_path: str) -> Dict[str, Any]:
        """
        Parses a local workflow YAML file to extract dispatch inputs.
        workflow_path is like '.github/workflows/main.yml'
        """
        full_path = self.project_dir / workflow_path
        if not full_path.exists():
            return {}

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Handle 'on' key which is parsed as boolean True by PyYAML 1.1 if not quoted
            on_data = data.get("on")
            if on_data is None:
                on_data = data.get(True, {})

            if isinstance(on_data, str):
                # on: push
                return {}

            if isinstance(on_data, list):
                # on: [push, pull_request]
                return {}

            dispatch = on_data.get("workflow_dispatch")
            if dispatch is None:
                return {}

            # If dispatch is just null/empty, it means no inputs
            if not dispatch:
                return {}

            return dispatch.get("inputs", {})

        except Exception:
            return {}
