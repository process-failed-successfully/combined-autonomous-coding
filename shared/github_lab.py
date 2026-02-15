import requests
import sys
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class GitHubLabManager:
    """Manages GitHub Lab operations: user, repo, search, gists, tree, raw."""

    API_BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def _get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Resource not found: {url}")
            if e.response.status_code == 401:
                raise ValueError("Unauthorized. Please check your GITHUB_TOKEN.")
            if e.response.status_code == 403:
                raise ValueError("Forbidden (Rate Limit Exceeded or Access Denied).")
            raise
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {e}")

    def get_user(self, username: str) -> Dict[str, Any]:
        """Fetches public user information."""
        url = f"{self.API_BASE_URL}/users/{username}"
        return self._get_json(url)

    def get_repo(self, owner_repo: str) -> Dict[str, Any]:
        """Fetches repository details. format: owner/repo"""
        if "/" not in owner_repo:
            raise ValueError("Repository must be in format 'owner/repo'")
        url = f"{self.API_BASE_URL}/repos/{owner_repo}"
        return self._get_json(url)

    def search_repos(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches for repositories."""
        url = f"{self.API_BASE_URL}/search/repositories"
        params = {"q": query, "per_page": limit}
        data = self._get_json(url, params=params)
        return data.get("items", [])

    def get_gists(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetches public gists for a user."""
        url = f"{self.API_BASE_URL}/users/{username}/gists"
        params = {"per_page": limit}
        return self._get_json(url, params=params)

    def get_tree(self, owner_repo: str, path: str = "") -> List[Dict[str, Any]]:
        """Fetches file tree for a repository path."""
        if "/" not in owner_repo:
            raise ValueError("Repository must be in format 'owner/repo'")

        url = f"{self.API_BASE_URL}/repos/{owner_repo}/contents/{path}"
        data = self._get_json(url)

        # If path points to a file, it returns a dict, not a list. Wrap it.
        if isinstance(data, dict):
            return [data]
        return data

    def get_raw(self, owner_repo: str, path: str) -> str:
        """Fetches raw file content."""
        if "/" not in owner_repo:
            raise ValueError("Repository must be in format 'owner/repo'")

        url = f"{self.API_BASE_URL}/repos/{owner_repo}/contents/{path}"
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.raw"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                 raise ValueError(f"File not found: {path} in {owner_repo}")
            raise
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {e}")

def run_github_lab_logic(args) -> bool:
    """CLI handler for GitHub Lab."""
    # Attempt to use token from args if provided (though not currently exposed in main.py for this command)
    # or fall back to environment variable.
    token = getattr(args, 'token', None)
    manager = GitHubLabManager(token=token)

    try:
        if args.action == "user":
            user = manager.get_user(args.username)
            print(f"--- User: {user.get('login')} ---")
            print(f"Name: {user.get('name')}")
            print(f"Bio: {user.get('bio')}")
            print(f"Location: {user.get('location')}")
            print(f"Public Repos: {user.get('public_repos')}")
            print(f"Followers: {user.get('followers')}")
            print(f"Blog: {user.get('blog')}")
            print(f"URL: {user.get('html_url')}")

        elif args.action == "repo":
            repo = manager.get_repo(args.repo)
            print(f"--- Repo: {repo.get('full_name')} ---")
            print(f"Description: {repo.get('description')}")
            print(f"Stars: {repo.get('stargazers_count')}")
            print(f"Forks: {repo.get('forks_count')}")
            print(f"Open Issues: {repo.get('open_issues_count')}")
            print(f"Language: {repo.get('language')}")
            print(f"License: {repo.get('license', {}).get('name') if repo.get('license') else 'None'}")
            print(f"URL: {repo.get('html_url')}")

        elif args.action == "search":
            limit = getattr(args, 'limit', 10)
            results = manager.search_repos(args.query, limit=limit)
            print(f"--- Search Results for '{args.query}' (Top {limit}) ---")
            for r in results:
                print(f"\n{r.get('full_name')} (Stars: {r.get('stargazers_count')})")
                print(f"  {r.get('description')}")
                print(f"  URL: {r.get('html_url')}")

        elif args.action == "gists":
            limit = getattr(args, 'limit', 10)
            gists = manager.get_gists(args.username, limit=limit)
            print(f"--- Gists for {args.username} (Top {limit}) ---")
            if not gists:
                print("No public gists found.")
            for g in gists:
                files = ", ".join(g.get('files', {}).keys())
                print(f"\nID: {g.get('id')}")
                print(f"  Description: {g.get('description') or '(no description)'}")
                print(f"  Files: {files}")
                print(f"  URL: {g.get('html_url')}")

        elif args.action == "tree":
            items = manager.get_tree(args.repo, args.path or "")
            print(f"--- Tree: {args.repo}/{args.path or ''} ---")
            # Sort: directories first, then files
            items.sort(key=lambda x: (x.get('type') != 'dir', x.get('name')))

            for item in items:
                type_marker = "📁" if item.get('type') == 'dir' else "📄"
                size = f"({item.get('size')} bytes)" if item.get('size') else ""
                print(f"{type_marker} {item.get('name')} {size}")

        elif args.action == "raw":
            content = manager.get_raw(args.repo, args.path)
            print(content)

        return True

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
