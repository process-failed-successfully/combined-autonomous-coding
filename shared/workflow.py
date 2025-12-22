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
        res = subprocess.run(["git", "remote", "get-url", "origin"],
                             cwd=project_dir, check=True, stdout=subprocess.PIPE, text=True)
        remote_url = res.stdout.strip()
        gh_helper = GitHubClient()
        return gh_helper.get_repo_info_from_remote(remote_url)
    except Exception as e:
        logger.warning(f"Failed to get remote info: {e}")
        return None, None, None


def _create_pr(config: Config, current_branch: str) -> Optional[str]:
    """
    Creates a PR and returns the URL. Returns None on failure.
    """
    host, owner, repo = _get_remote_info(config.project_dir)
    if not (host and owner and repo):
        logger.warning("Could not determine repository info for PR creation.")
        return None

    try:
        gh_client = GitHubClient(host=host)

        # Detect default branch
        base_branch = "main"
        repo_meta = gh_client.get_repo_metadata(owner, repo)
        if repo_meta and "default_branch" in repo_meta:
            base_branch = repo_meta["default_branch"]
            logger.info(f"Detected default branch '{base_branch}' for repo {owner}/{repo}")

        # Avoid PR from main to main
        if current_branch == base_branch:
            logger.warning(f"Current branch is same as base branch ({base_branch}). Skipping PR.")
            return None

        # Read PR Description from file if exists
        pr_body = f"Automated PR for Jira Ticket {config.jira_ticket_key}."
        pr_desc_file = config.project_dir / "PR_DESCRIPTION.md"
        if pr_desc_file.exists():
            try:
                pr_body = pr_desc_file.read_text().strip()
                logger.info(f"Loaded PR description from {pr_desc_file}")
            except Exception as e:
                logger.warning(f"Failed to read {pr_desc_file}: {e}")

        pr_url = gh_client.create_pr(
            owner, repo,
            title=f"Fixes {config.jira_ticket_key}",
            body=pr_body,
            head=current_branch,
            base=base_branch
        )
        return pr_url
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
