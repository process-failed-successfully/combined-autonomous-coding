"""
Git Utilities
=============

Functions for managing git state and ensuring safe branching for agents.
"""

import logging
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)

def configure_git_auth(token: str, host: str = "github.com", username: str = "x-access-token") -> bool:
    """
    Configure global git to use the provided token for authentication.
    Uses 'insteadOf' to transparently rewrite URL.
    """
    try:
        # Construct the authenticated URL base
        # e.g. https://x-access-token:MYTOKEN@github.com/
        safe_token = token.strip()
        safe_host = host.strip()
        safe_user = username.strip()

        logger.info(f"Configuring Git Auth for host: {safe_host} (User: {safe_user})")

        # Configure rewrite rule
        # git config --global url."https://${user}:${token}@${host}/".insteadOf "https://${host}/"
        
        auth_url = f"https://{safe_user}:{safe_token}@{safe_host}/"
        base_url = f"https://{safe_host}/"

        cmd = [
            "config",
            "--global",
            f"url.{auth_url}.insteadOf",
            base_url
        ]
        
        subprocess.run(["git"] + cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception as e:
        logger.error(f"Failed to configure git auth: {e}")
        return False



def run_git(cmd: list[str], cwd: Path) -> bool:
    """Run a git command and return success status."""
    try:
        subprocess.run(
            ["git"] + cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.debug(f"Git command failed: {cmd} -> {e.stderr.decode().strip()}")
        return False
    except Exception as e:
        logger.error(f"Git execution error: {e}")
        return False


def ensure_git_safe(project_dir: Path, ticket_key: str = None) -> None:
    """
    Ensure the project is in a safe git state.
    - If not a repo: init, commit, checkout branch.
    - If repo: checkout new timestamped branch.
    """
    if not (project_dir / ".git").exists():
        logger.info("Initializing new git repository...")
        run_git(["init"], project_dir)
        run_git(["add", "."], project_dir)
        run_git(["commit", "-m", "Initial commit"], project_dir)
        # We ensure we are on main
        run_git(["branch", "-M", "main"], project_dir)

    # Check if we are already on an agent branch?
    # Maybe. But safer to always create a new one for a new run session.

    timestamp = int(time.time())
    if ticket_key:
        # Sanitize ticket key
        safe_ticket = "".join(c if c.isalnum() or c in "-_" else "" for c in ticket_key)
        branch_name = f"agent/{safe_ticket}-{timestamp}"
    else:
        branch_name = f"agent/session-{timestamp}"

    logger.info(f"Checking out safe branch: {branch_name}")

    # Create and checkout
    # -b creates it.
    if run_git(["checkout", "-b", branch_name], project_dir):
        logger.info(f"Switched to new branch: {branch_name}")
    else:
        logger.warning(f"Failed to create/switch to branch {branch_name}. Check logs.")


def push_branch(project_dir: Path, branch_name: str = None) -> bool:
    """Push the current branch to origin."""
    try:
        if not branch_name:
            # Get current branch
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_dir,
                check=True,
                stdout=subprocess.PIPE,
                text=True
            )
            branch_name = res.stdout.strip()

        logger.info(f"Pushing branch {branch_name} to origin...")
        run_git(["push", "-u", "origin", branch_name], project_dir)
        return True
    except Exception as e:
        logger.error(f"Failed to push branch: {e}")
        return False


def clone_repo(url: str, dest_path: Path) -> bool:
    """Clone a repository to the destination path."""
    try:
        logger.info(f"Cloning {url} to {dest_path}...")
        subprocess.run(
            ["git", "clone", url, str(dest_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repo {url}: {e.stderr.decode().strip()}")
        return False
    except Exception as e:
        logger.error(f"Error cloning repo: {e}")
        return False
