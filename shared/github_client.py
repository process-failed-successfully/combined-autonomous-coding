import os
import requests
from urllib.parse import urlparse

class GitHubClient:
    """A client for interacting with the GitHub API."""

    def __init__(self, token: str, host: str = "github.com"):
        self.token = token
        self.host = host
        if host == "github.com":
            self.api_base_url = "https://api.github.com"
        else:
            self.api_base_url = f"https://{host}/api/v3"

    def _get_headers(self):
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def _get_repo_owner_and_name(self, project_dir):
        import subprocess
        try:
            # Get the remote URL
            result = subprocess.run(
                ["git", "-C", str(project_dir), "config", "--get", "remote.origin.url"],
                capture_output=True, text=True, check=True
            )
            remote_url = result.stdout.strip()

            # Parse the URL to get the owner and repo name
            if remote_url.startswith("git@"):
                # SSH URL format: git@hostname:owner/repo.git
                path = remote_url.split(":")[1]
                owner, repo = path.replace(".git", "").split("/")
            else:
                # HTTPS URL format: https://hostname/owner/repo.git
                parsed_url = urlparse(remote_url)
                path_parts = parsed_url.path.strip("/").replace(".git", "").split("/")
                if len(path_parts) >= 2:
                    owner, repo = path_parts[-2], path_parts[-1]
                else:
                    return None, None
            return owner, repo
        except (subprocess.CalledProcessError, IndexError):
            return None, None

    def create_pull_request(self, project_dir, title: str, body: str, head_branch: str, base_branch: str):
        """Creates a pull request on GitHub."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls"
        headers = self._get_headers()
        data = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)

        if response.status_code == 201:
            return response.json()
        else:
            response.raise_for_status()

    def list_workflows(self, project_dir):
        """Lists GitHub Actions workflows."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/actions/workflows"
        headers = self._get_headers()

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def list_workflow_runs(self, project_dir, workflow_id, per_page=20):
        """Lists runs for a specific workflow."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        headers = self._get_headers()
        params = {"per_page": per_page}

        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def get_workflow_run_jobs(self, project_dir, run_id):
        """Gets jobs for a workflow run."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
        headers = self._get_headers()

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def trigger_workflow_dispatch(self, project_dir, workflow_id, ref, inputs=None):
        """Triggers a workflow dispatch event."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        headers = self._get_headers()
        data = {
            "ref": ref
        }
        if inputs:
            data["inputs"] = inputs

        response = requests.post(url, headers=headers, json=data, timeout=10)
        # 204 No Content is success
        if response.status_code == 204:
            return True
        else:
            response.raise_for_status()

    def get_issues(self, project_dir, state="open", assignee=None):
        """Fetches issues from GitHub."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/issues"
        headers = self._get_headers()
        params = {
            "state": state,
            "per_page": 100,
        }
        if assignee:
            params["assignee"] = assignee

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            # Filter out pull requests as they are also returned by the issues endpoint
            issues = [issue for issue in response.json() if "pull_request" not in issue]
            return issues
        else:
            response.raise_for_status()

    def get_issue(self, project_dir, issue_number):
        """Fetches a single issue by number."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        headers = self._get_headers()

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def list_pull_requests(self, project_dir, state="open"):
        """Lists pull requests for the repository."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls"
        headers = self._get_headers()
        params = {"state": state, "per_page": 50}

        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def get_pull_request(self, project_dir, pr_number):
        """Fetches details of a specific pull request."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = self._get_headers()

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def get_pull_request_reviews(self, project_dir, pr_number):
        """Fetches reviews for a pull request."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        headers = self._get_headers()

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def get_pull_request_checks(self, project_dir, pr_ref):
        """Fetches check runs for a specific PR reference (SHA)."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/commits/{pr_ref}/check-runs"
        headers = self._get_headers()

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Not all repos have check runs enabled or accessible this way, fail gracefully?
            # Or assume it might be check-suites.
            # Let's just raise for now.
            response.raise_for_status()

    def merge_pull_request(self, project_dir, pr_number, method="merge"):
        """Merges a pull request."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
        headers = self._get_headers()
        data = {"merge_method": method}

        response = requests.put(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def close_pull_request(self, project_dir, pr_number):
        """Closes a pull request without merging."""
        owner, repo = self._get_repo_owner_and_name(project_dir)
        if not owner or not repo:
            raise ValueError("Could not determine the repository owner and name from the git remote URL.")

        url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = self._get_headers()
        data = {"state": "closed"}

        response = requests.patch(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
