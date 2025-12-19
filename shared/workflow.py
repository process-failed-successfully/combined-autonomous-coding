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
            try:
                # Try to guess owner/repo from remote origin
                res = subprocess.run(["git", "remote", "get-url", "origin"], 
                                     cwd=config.project_dir, check=True, stdout=subprocess.PIPE, text=True)
                remote_url = res.stdout.strip()
                
                # Use a temporary client to parse the remote
                gh_helper = GitHubClient()
                host, owner, repo = gh_helper.get_repo_info_from_remote(remote_url)
                
                if host and owner and repo:
                    # Re-instantiate client with correct host
                    gh_client = GitHubClient(host=host)
                    
                    # Detect default branch
                    base_branch = "main"
                    repo_meta = gh_client.get_repo_metadata(owner, repo)
                    if repo_meta and "default_branch" in repo_meta:
                        base_branch = repo_meta["default_branch"]
                        logger.info(f"Detected default branch '{base_branch}' for repo {owner}/{repo}")
                    else:
                        logger.warning(f"Failed to detect default branch for {owner}/{repo}. Falling back to '{base_branch}'.")

                    # Get current branch
                    res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                                        cwd=config.project_dir, check=True, stdout=subprocess.PIPE, text=True)
                    current_branch = res.stdout.strip()
                    
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
                    if pr_url:
                        pr_link = pr_url
                else:
                    logger.warning(f"Could not determine GitHub host/owner/repo from sanitized URL: {sanitize_url(remote_url)}")
            except Exception as e:
                logger.error(f"Error during PR creation: {e}")

        # 3. Transition Jira Ticket
        j_client = JiraClient(config.jira)
        done_status = config.jira.status_map.get("done", "Code Review") if config.jira.status_map else "Code Review"
        logger.info(f"Transitioning Jira Ticket {config.jira_ticket_key} to '{done_status}'...")
        j_client.transition_issue(config.jira_ticket_key, done_status)
        
        # 4. Add Jira Comment
        # Read Jira Comment from file if exists
        jira_comment_body = f"Agent has completed the work. Please review.\nPR: {pr_link}"
        jira_comment_file = config.project_dir / "JIRA_COMMENT.txt"
        if jira_comment_file.exists():
            try:
                custom_comment = jira_comment_file.read_text().strip()
                if custom_comment:
                    jira_comment_body = f"{custom_comment}\nPR: {pr_link}"
                    logger.info(f"Loaded Jira comment from {jira_comment_file}")
            except Exception as e:
                logger.warning(f"Failed to read {jira_comment_file}: {e}")

        # Check for duplicate comments
        try:
            issue = j_client.get_issue(config.jira_ticket_key)
            existing_comments = issue.fields.comment.comments if hasattr(issue.fields, 'comment') else []
            is_duplicate = False
            for comment in existing_comments:
                if pr_link != "No PR created" and pr_link in comment.body:
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
