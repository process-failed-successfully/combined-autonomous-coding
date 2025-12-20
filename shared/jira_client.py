"""
Jira Client
===========

Client for interacting with Jira (Cloud and Self-Hosted).
"""

import logging
from typing import Optional, List, Any
from jira import JIRA, JIRAError
from shared.config import JiraConfig

logger = logging.getLogger(__name__)


class JiraClient:
    """
    Wrapper around the encryption `jira` library to provide simplified access
    matching the agent's needs.
    """

    def __init__(self, config: JiraConfig):
        self.config = config
        self._client: Optional[JIRA] = None
        self._connect()

    def _connect(self):
        """Establish connection to Jira."""
        try:
            logger.info(f"Connecting to Jira at {self.config.url}...")
            # JIRA library handles Basic Auth (user, token/password)
            self._client = JIRA(
                server=self.config.url,
                basic_auth=(self.config.email, self.config.token),
            )
            # Verify connection (optional, lightweight check)
            user = self._client.myself()
            logger.info(f"Connected to Jira as {user.get('displayName')}")
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {e}")
            raise

    def get_issue(self, issue_key: str) -> Optional[Any]:
        """Fetch a single issue by key (e.g., PROJ-123)."""
        if not self._client:
            raise RuntimeError("Jira Client not connected")
        try:
            issue = self._client.issue(issue_key)
            return issue
        except JIRAError as e:
            if e.status_code == 404:
                logger.warning(f"Issue {issue_key} not found.")
                return None
            logger.error(f"Error fetching issue {issue_key}: {e}")
            raise

    def search_issues(self, jql: str, max_results: int = 10) -> List[Any]:
        """Search for issues using JQL."""
        if not self._client:
            return []
        try:
            issues = self._client.search_issues(jql, maxResults=max_results)
            return issues
        except JIRAError as e:
            logger.error(f"Error searching issues with JQL '{jql}': {e}")
            return []

    def get_first_todo_by_label(self, label: str) -> Optional[Any]:
        """Find the first 'To Do' issue with the given label."""
        # Note: status category 'To Do' is standard, but names vary.
        # We rely on "statusCategory = 'To Do'" or explicit names if needed.
        # JQL: labels = "label" AND statusCategory = "To Do"
        # Using statusCategory is safer than rigid names.
        jql = f'labels = "{label}" AND statusCategory = "To Do" ORDER BY priority DESC, created ASC'
        issues = self.search_issues(jql, max_results=1)
        if issues:
            return issues[0]
        return None

    def transition_issue(self, issue_key: str, target_status: str) -> bool:
        """
        Transition an issue to a new status (by name).
        Tries to find a transition that matches the target_status name.
        """
        if not self._client:
            return False
        try:
            # We need to find the transition ID for the name
            transitions = self._client.transitions(issue_key)
            t_id = None
            for t in transitions:
                if t["name"].lower() == target_status.lower():
                    t_id = t["id"]
                    break

            if not t_id:
                logger.warning(
                    f"Transition to '{target_status}' not found for {issue_key}. "
                    f"Available: {[t['name'] for t in transitions]}"
                )
                return False

            self._client.transition_issue(issue_key, t_id)
            logger.info(f"Transitioned {issue_key} to '{target_status}'")
            return True
        except JIRAError as e:
            logger.error(f"Error transitioning issue {issue_key}: {e}")
            return False

    def add_comment(self, issue_key: str, body: str) -> bool:
        """Add a comment to the issue."""
        if not self._client:
            return False
        try:
            self._client.add_comment(issue_key, body)
            logger.info(f"Added comment to {issue_key}")
            return True
        except JIRAError as e:
            logger.error(f"Error adding comment to {issue_key}: {e}")
            return False
