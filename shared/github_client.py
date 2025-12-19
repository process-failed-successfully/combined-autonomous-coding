import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GIT_TOKEN") or os.environ.get("GITHUB_TOKEN")
        self.api_base = "https://api.github.com"

    def create_pr(self, owner: str, repo: str, title: str, body: str, head: str, base: str = "main") -> Optional[str]:
        """
        Create a Pull Request.
        Returns the HTML URL of the created PR, or None if failed.
        """
        if not self.token:
            logger.warning("No GIT_TOKEN found. Cannot create Pull Request.")
            return None

        url = f"{self.api_base}/repos/{owner}/{repo}/pulls"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }

        try:
            logger.info(f"Creating PR in {owner}/{repo}: {title}")
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 201:
                pr_data = response.json()
                pr_url = pr_data.get("html_url")
                logger.info(f"Pull Request created successfully: {pr_url}")
                return pr_url
            else:
                logger.error(f"Failed to create PR: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating PR: {e}")
            return None

    def get_repo_info_from_remote(self, remote_url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract owner and repo name from remote URL.
        Supports:
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        """
        try:
            clean_url = remote_url.strip()
            if clean_url.endswith(".git"):
                clean_url = clean_url[:-4]
            
            if "github.com" in clean_url:
                parts = clean_url.split("github.com")[-1]
                parts = parts.strip("/:").split("/")
                if len(parts) >= 2:
                    return parts[0], parts[1]
            return None, None
        except Exception:
            return None, None
