import subprocess
import requests
from pathlib import Path
import re

class GitHubClient:
    def __init__(self, token: str, host: str = "github.com"):
        self.token = token
        self.host = host
        self.api_base_url = f"https://api.{host}" if host == "github.com" else f"https://{host}/api/v3"

    def _get_repo_owner_and_name(self, project_dir: Path):
        try:
            result = subprocess.run(
                ["git", "-C", str(project_dir), "remote", "get-url", "origin"],
                capture_output=True, text=True, check=True
            )
            remote_url = result.stdout.strip()

            # Handle SSH URLs (e.g., git@github.com:owner/repo.git)
            ssh_match = re.search(r'git@[\w.-]+:([\w-]+)/([\w.-]+?)(?:\.git)?$', remote_url)
            if ssh_match:
                return ssh_match.group(1), ssh_match.group(2)

            # Handle HTTPS URLs (e.g., https://github.com/owner/repo.git)
            https_match = re.search(r'https://[\w.-]+/([\w-]+)/([\w.-]+?)(?:\.git)?$', remote_url)
            if https_match:
                return https_match.group(1), https_match.group(2)

            raise ValueError(f"Could not parse repository owner and name from remote URL: {remote_url}")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Could not get remote URL: {e.stderr}")

    def create_pull_request(self, project_dir: Path, title: str, body: str, head_branch: str, base_branch: str):
        """
        Creates a pull request on GitHub.

        Args:
            project_dir: The path to the local git repository.
            title: The title of the pull request.
            body: The body content of the pull request.
            head_branch: The name of the branch with the changes.
            base_branch: The name of the branch to merge into.

        Returns:
            A dictionary representing the JSON response from the GitHub API.

        Raises:
            ValueError: If the repository owner and name cannot be determined.
            requests.exceptions.RequestException: For network or API errors.
        """
        owner, repo = self._get_repo_owner_and_name(project_dir)
        url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        data = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
        }
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        return response.json()
