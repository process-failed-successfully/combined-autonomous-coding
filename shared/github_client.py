import os
import requests
import json
from typing import Optional, Dict, Any

class GitHubClient:
    """A client for interacting with the GitHub API."""

    def __init__(self, token: Optional[str] = None, host: str = "github.com"):
        """
        Initializes the GitHub client.

        Args:
            token: The GitHub personal access token. If not provided, it will
                   try to fall back to the GITHUB_TOKEN environment variable.
            host: The GitHub host. Defaults to 'github.com'. This can be changed
                  for GitHub Enterprise instances.
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.host = host
        if self.host == "github.com":
            self.api_base_url = "https://api.github.com"
        else:
            self.api_base_url = f"https://{self.host}/api/v3"

        if not self.token:
            raise ValueError("GitHub token is required. Please provide it directly or set the GITHUB_TOKEN environment variable.")

        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    def create_pull_request(self, owner: str, repo: str, title: str, body: str, head: str, base: str) -> Dict[str, Any]:
        """
        Creates a new pull request on GitHub.

        Args:
            owner: The owner of the repository.
            repo: The name of the repository.
            title: The title of the pull request.
            body: The body content of the pull request.
            head: The name of the branch where your changes are implemented.
            base: The name of the branch you want the changes pulled into.

        Returns:
            A dictionary representing the JSON response from the GitHub API.

        Raises:
            requests.exceptions.RequestException: For network errors or HTTP error statuses.
        """
        pr_url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }

        response = requests.post(pr_url, headers=self.headers, data=json.dumps(payload))
        response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
