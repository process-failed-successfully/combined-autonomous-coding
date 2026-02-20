"""
Git Utilities
=============

Functions for managing git state and ensuring safe branching for agents.
"""

import logging
import subprocess
import time
import re
from pathlib import Path
from typing import Optional
from shared.utils import sanitize_text, sanitize_url

logger = logging.getLogger(__name__)


def is_git_safeguard_active() -> bool:
    """Check if the git push safeguard wrapper is active."""
    try:
        # Check if /usr/local/bin/git is the wrapper
        # Or check if git.real exists
        return Path("/usr/bin/git.real").exists()
    except Exception:
        return False


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
    except subprocess.CalledProcessError as e:
        # Do not log 'e' directly as it contains the command with the token
        logger.error(f"Failed to configure git auth. Command failed with return code {e.returncode}.")
        if e.stderr:
            logger.error(f"Git error output: {e.stderr.decode('utf-8', errors='replace').strip()}")
        return False
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
        logger.debug(f"Git command failed: {sanitize_text(str(cmd))} -> {sanitize_text(e.stderr.decode().strip())}")
        return False
    except Exception as e:
        logger.error(f"Git execution error: {e}")
        return False


def ensure_git_safe(project_dir: Path, ticket_key: Optional[str] = None) -> None:
    """
    Ensure the project is in a safe git state.
    - If a .agent_branch file exists, check out that branch.
    - If not a repo: init, commit, checkout a new branch.
    - If repo without .agent_branch: checkout new timestamped branch.
    """
    agent_branch_file = project_dir / ".agent_branch"

    if agent_branch_file.exists():
        try:
            agent_branch = agent_branch_file.read_text().strip()
            if agent_branch:
                logger.info(f"Found agent branch file. Attempting to switch to '{agent_branch}'...")
                # Verify branch exists before checking out
                if run_git(["rev-parse", "--verify", agent_branch], project_dir):
                    if run_git(["checkout", agent_branch], project_dir):
                        logger.info(f"Successfully checked out existing agent branch: {agent_branch}")
                        return  # Branch is set, our work is done.
                    else:
                        logger.warning(f"Failed to checkout branch '{agent_branch}'. Will proceed with default behavior.")
                else:
                    logger.warning(f"Branch '{agent_branch}' from .agent_branch file not found. Will proceed with default behavior.")
        except Exception as e:
            logger.error(f"Error reading .agent_branch file: {e}. Will proceed with default behavior.")

    if not (project_dir / ".git").exists():
        logger.info("Initializing new git repository...")
        if is_git_safeguard_active():
            logger.info("Git push safeguard is ACTIVE.")
        run_git(["init"], project_dir)
        run_git(["add", "."], project_dir)
        run_git(["commit", "-m", "Initial commit"], project_dir)
        # We ensure we are on main
        run_git(["branch", "-M", "main"], project_dir)

    # If .agent_branch logic didn't succeed, fall back to creating a new branch.
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


def push_branch(project_dir: Path, branch_name: Optional[str] = None) -> bool:
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

        # RESTRICTED BRANCH CHECK
        restricted_branches = ["main", "master"]
        if branch_name.lower() in restricted_branches:
            logger.error(f"ABORTED: Attempted to push to restricted branch '{branch_name}'.")
            # We raise an error or return False. Returning False is consistent with run_git pattern.
            return False

        logger.info(f"Pushing branch {branch_name} to origin...")
        return run_git(["push", "-u", "origin", branch_name], project_dir)
    except Exception as e:
        logger.error(f"Failed to push branch: {e}")
        return False


def clone_repo(url: str, dest_path: Path) -> bool:
    """Clone a repository to the destination path."""
    try:
        logger.info(f"Cloning {sanitize_url(url)} to {dest_path}...")
        subprocess.run(
            ["git", "clone", url, str(dest_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repo {sanitize_url(url)}: {e.stderr.decode().strip()}")
        return False
    except Exception as e:
        logger.error(f"Error cloning repo: {e}")
        return False


def get_current_branch(project_dir: Path) -> Optional[str]:
    """Gets the current active git branch name."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_dir,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
            stderr=subprocess.PIPE,
        )
        branch_name = res.stdout.strip()
        return branch_name if branch_name else None
    except subprocess.CalledProcessError as e:
        logger.debug(f"Could not get current branch: {e.stderr.strip()}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting the current branch: {e}")
        return None


def get_git_log(project_dir: Path, limit: int = 50) -> list[dict]:
    """
    Fetches the git log.
    Returns a list of dicts: {"hash", "author", "date", "message"}
    """
    try:
        # %h: abbreviated hash, %an: author name, %ad: author date, %s: subject
        cmd = ["git", "log", f"-n{limit}", "--pretty=format:%h|%an|%ad|%s", "--date=short"]
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True
        )
        logs = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 3)
            if len(parts) == 4:
                logs.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                })
        return logs
    except Exception as e:
        logger.error(f"Error getting git log: {e}")
        return []


def get_commit_details(project_dir: Path, commit_hash: str) -> str:
    """Fetches details for a specific commit."""
    try:
        cmd = ["git", "show", "--stat", commit_hash]
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        logger.error(f"Error getting commit details: {e}")
        return f"Error loading details for {commit_hash}"


def get_git_status(project_dir: Path) -> list[dict]:
    """
    Returns a list of file status objects.
    Format: [{"path": "file.py", "status_code": "M ", "staged": True}, ...]
    """
    try:
        # porcelain gives XY PATH
        cmd = ["git", "status", "--porcelain"]
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True
        )
        files = []
        for line in result.stdout.strip().split('\n'):
            if not line or len(line) < 4:
                continue

            # Extract XY and Path
            # porcelain format is fixed width for XY (2 chars) then space then path
            # But if path has spaces it might be quoted? --porcelain v1 quotes paths.
            # v1: XY PATH
            status_code = line[:2]
            path = line[3:].strip('"') # Simple unquote for now

            # Determine staged status
            # X (index), Y (worktree)
            # M_ -> Staged
            # _M -> Unstaged
            # MM -> Both
            # ?? -> Untracked (Unstaged)
            # A_ -> Added (Staged)

            index_status = status_code[0]
            # worktree_status = status_code[1] # Unused

            files.append({
                "path": path,
                "status_code": status_code,
                "staged": index_status not in [' ', '?', '!']
            })
        return files
    except Exception as e:
        logger.error(f"Error getting git status: {e}")
        return []


def stage_file(project_dir: Path, file_path: str) -> bool:
    """Stages a file."""
    return run_git(["add", file_path], project_dir)


def unstage_file(project_dir: Path, file_path: str) -> bool:
    """Unstages a file (git restore --staged)."""
    return run_git(["restore", "--staged", file_path], project_dir)


def commit_changes(project_dir: Path, message: str) -> bool:
    """Commits staged changes."""
    return run_git(["commit", "-m", message], project_dir)


def discard_changes(project_dir: Path, file_path: str) -> bool:
    """Discards changes (checkout or clean)."""
    # If untracked, use clean. If modified, use restore.
    # We can try restore first, if it fails try clean?
    # Or check status first.
    # For simplicity, let's try restore then clean.
    if run_git(["restore", file_path], project_dir):
        return True
    return run_git(["clean", "-f", file_path], project_dir)


def pull_changes(project_dir: Path) -> bool:
    """Pulls changes from origin."""
    return run_git(["pull"], project_dir)


def get_all_git_files(project_dir: Path) -> list[str]:
    """
    Returns a list of all files in the repository (tracked + untracked),
    excluding ignored files. Paths are relative to project_dir.
    """
    try:
        # Combined: Tracked + Untracked (respecting ignores)
        # -c: cached (tracked)
        # -o: others (untracked)
        # --exclude-standard: respect .gitignore
        cmd = ["git", "ls-files", "-z", "-c", "-o", "--exclude-standard"]
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True
        )
        files = result.stdout.split('\0')

        # Remove empty strings and duplicates
        all_files = set(files)
        if '' in all_files:
            all_files.remove('')

        return sorted(list(all_files))

    except Exception as e:
        logger.error(f"Error listing git files: {e}")
        return []


def get_file_diff(project_dir: Path, file_path: str, staged: bool = False) -> str:
    """
    Returns the diff for a specific file.
    If staged is True, returns cached diff.
    If file is untracked, returns file content as a new file diff.
    """
    try:
        cmd = ["git", "diff", "--no-color"]
        if staged:
            cmd.append("--cached")

        cmd.append("--") # Separator
        cmd.append(file_path)

        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True
        )

        diff = result.stdout

        # If no diff (and not error), maybe it's untracked or new
        if not diff and result.returncode == 0:
            # Check if untracked
            cmd_untracked = ["git", "ls-files", "--others", "--exclude-standard", "--", file_path]
            res_untracked = subprocess.run(
                cmd_untracked,
                cwd=project_dir,
                capture_output=True,
                text=True
            )
            if res_untracked.stdout.strip():
                # It is untracked, read content
                try:
                    content = (project_dir / file_path).read_text(encoding="utf-8", errors="replace")
                    return f"--- /dev/null\n+++ b/{file_path}\n@@ -0,0 +1,{len(content.splitlines())} @@\n{content}"
                except Exception as e:
                    return f"Error reading untracked file: {e}"

        return diff

    except Exception as e:
        logger.error(f"Error getting diff for {file_path}: {e}")
        return f"Error getting diff: {e}"


def get_git_stash_list(project_dir: Path) -> list[dict]:
    """
    Returns list of stashes: [{"index": "0", "name": "stash@{0}", "message": "..."}]
    """
    try:
        cmd = ["git", "stash", "list"]
        result = subprocess.run(
            cmd, cwd=project_dir, capture_output=True, text=True, check=True
        )
        stashes = []
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            # stash@{0}: On main: message...
            parts = line.split(':', 2)
            if len(parts) >= 2:
                name = parts[0].strip() # stash@{0}
                # extract index from stash@{N}
                m = re.search(r"stash@\{(\d+)\}", name)
                index = m.group(1) if m else "0"
                message = parts[2].strip() if len(parts) > 2 else ""
                stashes.append({"index": index, "name": name, "message": message})
        return stashes
    except Exception as e:
        logger.error(f"Error listing stashes: {e}")
        return []


def get_stash_show(project_dir: Path, stash_ref: str) -> str:
    """Returns the diff of a stash."""
    try:
        # -p for patch (diff)
        cmd = ["git", "stash", "show", "-p", stash_ref]
        result = subprocess.run(
            cmd, cwd=project_dir, capture_output=True, text=True, check=True
        )
        return result.stdout
    except Exception as e:
        logger.error(f"Error showing stash {stash_ref}: {e}")
        return f"Error showing stash {stash_ref}: {e}"


def stash_push(project_dir: Path, message: str) -> bool:
    """Push changes to a new stash."""
    cmd = ["stash", "push", "-m", message]
    return run_git(cmd, project_dir)


def stash_pop(project_dir: Path, stash_ref: str) -> bool:
    """Pop a stash (apply and drop)."""
    return run_git(["stash", "pop", stash_ref], project_dir)


def stash_apply(project_dir: Path, stash_ref: str) -> bool:
    """Apply a stash without dropping it."""
    return run_git(["stash", "apply", stash_ref], project_dir)


def stash_drop(project_dir: Path, stash_ref: str) -> bool:
    """Drop a stash."""
    return run_git(["stash", "drop", stash_ref], project_dir)


def get_git_graph_lines(project_dir: Path, limit: int = 100) -> list[str]:
    """
    Returns the raw output lines of 'git log --graph'.
    Includes ANSI color codes for visualization.
    """
    try:
        # --graph: text-based graph
        # --all: all branches
        # --color=always: keep ANSI codes for RichLog
        # --pretty: custom format
        cmd = [
            "git", "log", "--graph", "--all", "--color=always",
            f"-n{limit}", "--pretty=format:%h %d %s (%cr) <%an>"
        ]
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.splitlines()
    except Exception as e:
        logger.error(f"Error getting git graph: {e}")
        return [f"Error loading graph: {e}"]
