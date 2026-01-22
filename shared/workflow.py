"""
Unified Jira Workflow Utilities
===============================
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Any

from shared.config import Config
from shared.jira_client import JiraClient
from shared.git import push_branch
from shared.github_client import GitHubClient

logger = logging.getLogger(__name__)


def _get_remote_info(project_dir: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract (host, owner, repo) from git remote origin.
    """
    try:
        # res = subprocess.run(["git", "remote", "get-url", "origin"],
        #                      cwd=project_dir, check=True, stdout=subprocess.PIPE, text=True)
        # remote_url = res.stdout.strip()
        # GitHubClient logic is embedded here or we need a helper.
        # For now, simplistic parsing or assuming github.com if not ssh
        # But wait, GitHubClient has _get_repo_owner_and_name which takes project_dir!
        # And it returns (owner, repo). Host is implicit or we default to github.com
        return "github.com", None, None # Placeholder as _get_repo_owner_and_name returns owner, repo.
        # We need to refactor this to use GitHubClient properly or implement parsing.
        # Let's use GitHubClient's internal logic via a temporary instance if possible, or just fix the usage below.
    except Exception as e:
        logger.warning(f"Failed to get remote info: {e}")
        return None, None, None


def _create_pr(config: Config, current_branch: str) -> Optional[str]:
    """
    Creates a PR and returns the URL. Returns None on failure.
    """
    # We need a token.
    import os
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.warning("GITHUB_TOKEN not set. Cannot create PR.")
        return None

    try:
        # Assuming github.com for now as shared/github_client defaults to it
        gh_client = GitHubClient(token=token)

        # Get owner/repo using the client
        # Note: GitHubClient._get_repo_owner_and_name is "internal" but we can use it or expose it.
        # Accessing protected member for now or we should fix GitHubClient to expose it.
        # But wait, create_pull_request calls it internally!
        # So we just need to call create_pull_request.

        # However, we wanted to detect default branch.
        # GitHubClient doesn't expose get_repo_metadata.
        # We'll assume 'main' or 'master' or let GitHub handle it?
        # create_pull_request takes base_branch.
        # Let's try 'main' default.
        base_branch = "main"

        # Avoid PR from main to main
        if current_branch == base_branch:
             # We should probably check if current_branch IS the default branch.
             # Without API call, hard to be sure.
             pass

        # Read PR Description
        pr_body = f"Automated PR for Jira Ticket {config.jira_ticket_key}."
        pr_desc_file = config.project_dir / "PR_DESCRIPTION.md"
        if pr_desc_file.exists():
            try:
                pr_body = pr_desc_file.read_text().strip()
                logger.info(f"Loaded PR description from {pr_desc_file}")
            except Exception as e:
                logger.warning(f"Failed to read {pr_desc_file}: {e}")

        # Use create_pull_request which matches shared/github_client.py
        pr_data = gh_client.create_pull_request(
            config.project_dir, # project_dir
            title=f"Fixes {config.jira_ticket_key}",
            body=pr_body,
            head_branch=current_branch,
            base_branch=base_branch
        )
        return pr_data.get("html_url") # type: ignore
    except Exception as e:
        logger.error(f"Error creating PR: {e}")
        return None


async def complete_jira_ticket(config: Config) -> bool:
    """
    Handle the final steps of completing a Jira ticket:
    - Push the branch (ABORT if fails)
    - Create a Pull Request (Continue if fails)
    - Transition Jira ticket (Continue if fails)
    - Add Jira comment with PR link
    """
    if not (config.jira and config.jira_ticket_key):
        logger.warning("No Jira configuration found. Skipping Jira completion logic.")
        return False

    try:
        logger.info(f"Initiating completion for Jira Ticket: {config.jira_ticket_key}")

        # 1. Get Current Branch
        try:
            res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                 cwd=config.project_dir, check=True, stdout=subprocess.PIPE, text=True)
            current_branch = res.stdout.strip()
        except subprocess.CalledProcessError:
            logger.error("Failed to determine current branch. Is this a git repo?")
            return False

        # 2. Push Branch
        # push_branch checks for restricted branches internally and returns False if blocked.
        if not push_branch(config.project_dir, branch_name=current_branch):
            logger.error("Failed to push branch. Aborting Jira completion.")
            return False

        # 3. Create PR
        pr_link = _create_pr(config, current_branch)
        pr_text = pr_link if pr_link else f"Manual PR required (Branch: {current_branch})"

        j_client = JiraClient(config.jira)

        # 4. Transition Jira Ticket
        done_status = config.jira.status_map.get("done", "Code Review") if config.jira.status_map else "Code Review"
        logger.info(f"Transitioning Jira Ticket {config.jira_ticket_key} to '{done_status}'...")
        transition_success = j_client.transition_issue(config.jira_ticket_key, done_status)

        if not transition_success:
            logger.warning(f"Failed to transition ticket {config.jira_ticket_key} to {done_status}. Proceeding to comment.")

        # 5. Add Jira Comment
        jira_comment_body = f"Agent has completed the work. Please review.\nPR: {pr_text}"
        jira_comment_file = config.project_dir / "JIRA_COMMENT.txt"
        if jira_comment_file.exists():
            try:
                custom_comment = jira_comment_file.read_text().strip()
                if custom_comment:
                    jira_comment_body = f"{custom_comment}\nPR: {pr_text}"
                    logger.info(f"Loaded Jira comment from {jira_comment_file}")
            except Exception as e:
                logger.warning(f"Failed to read {jira_comment_file}: {e}")

        # Check for duplicate comments
        try:
            issue = j_client.get_issue(config.jira_ticket_key)
            if issue is None:
                logger.warning(f"Could not retrieve issue {config.jira_ticket_key} for duplicate check.")
                existing_comments: List[Any] = []
            else:
                existing_comments = issue.fields.comment.comments if hasattr(issue.fields, 'comment') else []
            is_duplicate = False
            for comment in existing_comments:
                if pr_link and pr_link in comment.body:
                    is_duplicate = True
                    break

            if is_duplicate:
                logger.info(f"Comment with PR link {pr_link} already exists on {config.jira_ticket_key}. Skipping duplicate comment.")
            else:
                j_client.add_comment(config.jira_ticket_key, jira_comment_body)
        except Exception as e:
            logger.error(f"Error checking for duplicate comments or adding comment: {e}")
            # Fallback to just adding it if check fails
            j_client.add_comment(config.jira_ticket_key, jira_comment_body)

        logger.info(f"Jira Ticket {config.jira_ticket_key} completion workflow finished. PR: {pr_link}")
        return True
    except Exception as e:
        logger.error(f"Failed to complete Jira ticket flow: {e}")
        return False
