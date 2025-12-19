"""
Unified Jira Workflow Utilities
===============================
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from shared.config import Config
from shared.jira_client import JiraClient
from shared.git import push_branch
from shared.github_client import GitHubClient
from shared.utils import sanitize_url

logger = logging.getLogger(__name__)

async def complete_jira_ticket(config: Config) -> bool:
    """
    Handle the final steps of completing a Jira ticket:
    - Push the branch
    - Create a Pull Request
    - Transition Jira ticket
    - Add Jira comment with PR link
    """
    if not (config.jira and config.jira_ticket_key):
        logger.warning("No Jira configuration found. Skipping Jira completion logic.")
        return False

    try:
        logger.info(f"Initiating completion for Jira Ticket: {config.jira_ticket_key}")
        
        # 1. Push Branch
        push_success = push_branch(config.project_dir)
        
        # 2. Create PR
        pr_link = "No PR created"
        if push_success:
            gh_client = GitHubClient()
            try:
                # Try to guess owner/repo from remote origin
                res = subprocess.run(["git", "remote", "get-url", "origin"], 
                                    cwd=config.project_dir, check=True, stdout=subprocess.PIPE, text=True)
                remote_url = res.stdout.strip()
                owner, repo = gh_client.get_repo_info_from_remote(remote_url)
                
                if owner and repo:
                    # Get current branch
                    res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                                        cwd=config.project_dir, check=True, stdout=subprocess.PIPE, text=True)
                    current_branch = res.stdout.strip()
                    
                    pr_url = gh_client.create_pr(
                        owner, repo, 
                        title=f"Fixes {config.jira_ticket_key}",
                        body=f"Automated PR for Jira Ticket {config.jira_ticket_key}.",
                        head=current_branch,
                        base="main"
                    )
                    if pr_url:
                        pr_link = pr_url
                else:
                    logger.warning(f"Could not determine GitHub owner/repo from sanitized URL: {sanitize_url(remote_url)}")
            except Exception as e:
                logger.error(f"Error during PR creation: {e}")

        # 3. Transition Jira Ticket
        j_client = JiraClient(config.jira)
        done_status = config.jira.status_map.get("done", "Code Review") if config.jira.status_map else "Code Review"
        logger.info(f"Transitioning Jira Ticket {config.jira_ticket_key} to '{done_status}'...")
        j_client.transition_issue(config.jira_ticket_key, done_status)
        
        # 4. Add Jira Comment
        j_client.add_comment(config.jira_ticket_key, f"Agent has completed the work. Please review.\nPR: {pr_link}")
        
        logger.info(f"Jira Ticket {config.jira_ticket_key} completion workflow finished. PR: {pr_link}")
        return True
    except Exception as e:
        logger.error(f"Failed to complete Jira ticket flow: {e}")
        return False
