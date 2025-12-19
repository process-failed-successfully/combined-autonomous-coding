import os
import logging
import requests
import re
from typing import Optional
from shared.utils import sanitize_url

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, token: Optional[str] = None, host: str = "github.com"):
        self.token = token or os.environ.get("GIT_TOKEN") or os.environ.get("GITHUB_TOKEN")
        self.host = host
        self._set_api_base()

    def _set_api_base(self):
        """Set the API base based on the host."""
        if self.host == "github.com":
            self.api_base = "https://api.github.com"
        else:
            # GitHub Enterprise uses /api/v3
            self.api_base = f"https://{self.host}/api/v3"

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
            logger.info(f"Creating PR in {owner}/{repo} ({self.host}): {title}")
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

    def get_repo_info_from_remote(self, remote_url: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract host, owner and repo name from remote URL.
        Supports:
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        - https://token@custom-domain.net/owner/repo.git
        Returns (host, owner, repo)
        """
        try:
            clean_url = remote_url.strip()
            if clean_url.endswith(".git"):
                clean_url = clean_url[:-4]
            
            # Pattern for HTTPS: https://[token@]host/owner/repo
            https_match = re.search(r"https?://(?:[^@/]+@)?(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>[^/]+)/?$", clean_url)
            if https_match:
                return https_match.group("host"), https_match.group("owner"), https_match.group("repo")

            # Pattern for SSH: git@host:owner/repo
            ssh_match = re.search(r"git@(?P<host>[^:]+):(?P<owner>[^/]+)/(?P<repo>[^/]+)/?$", clean_url)
            if ssh_match:
                return ssh_match.group("host"), ssh_match.group("owner"), ssh_match.group("repo")

            logger.warning(f"Failed to parse GitHub host/owner/repo from URL: {sanitize_url(clean_url)}")
            return None, None, None
        except Exception as e:
            logger.error(f"Error parsing remote URL: {e}")
            return None, None, None
