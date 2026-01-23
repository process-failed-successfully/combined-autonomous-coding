import subprocess
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class WorktreeManager:
    """Manages Git Worktrees for the agent."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.worktrees_dir = project_dir / "worktrees"
        self.git_cmd = shutil.which("git") or "git"

    def _run_git(self, args: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
        cwd = cwd or self.project_dir
        return subprocess.run(
            [self.git_cmd] + args,
            cwd=str(cwd),
            check=check,
            capture_output=True,
            text=True
        )

    def ensure_worktrees_dir(self):
        """Ensures the worktrees directory exists."""
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

    def list_worktrees(self) -> List[Dict[str, str]]:
        """Lists all worktrees managed by the agent (in the worktrees/ directory)."""
        try:
            result = self._run_git(["worktree", "list", "--porcelain"])
            worktrees = []
            current_worktree: Dict[str, str] = {}

            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    if current_worktree:
                        path = Path(current_worktree.get("worktree", ""))
                        # Filter to only show worktrees in our worktrees dir
                        if self.worktrees_dir.resolve() in path.resolve().parents:
                            current_worktree["name"] = path.name
                            worktrees.append(current_worktree)
                    current_worktree = {}
                else:
                    parts = line.split(" ", 1)
                    key = parts[0]
                    value = parts[1] if len(parts) > 1 else ""
                    current_worktree[key] = value

            # Append last one
            if current_worktree:
                path = Path(current_worktree.get("worktree", ""))
                if self.worktrees_dir.resolve() in path.resolve().parents:
                    current_worktree["name"] = path.name
                    worktrees.append(current_worktree)

            return worktrees
        except subprocess.CalledProcessError as e:
            logger.error(f"Error listing worktrees: {e.stderr}")
            return []

    def create(self, name: str, branch: Optional[str] = None) -> bool:
        """Creates a new worktree."""
        self.ensure_worktrees_dir()
        path = self.worktrees_dir / name
        if path.exists():
            raise FileExistsError(f"Worktree path {path} already exists.")

        branch = branch or name
        try:
            self._run_git(["worktree", "add", "-b", branch, str(path), "HEAD"])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating worktree: {e.stderr}")
            # Cleanup
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
            raise e

    def remove(self, name: str, force: bool = False) -> bool:
        """Removes a worktree."""
        path = self.worktrees_dir / name
        cmd = ["worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(name) # Git accepts the name/path

        try:
            self._run_git(cmd)
            # Ensure dir is gone
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error removing worktree: {e.stderr}")
            # If git fails, but we forced, maybe try to cleanup dir anyway if it's not a valid worktree
            if force and path.exists():
                try:
                     shutil.rmtree(path, ignore_errors=True)
                     return True
                except Exception:
                     pass
            raise e

    def get_status(self, name: str) -> str:
        """Gets the git status of a worktree."""
        path = self.worktrees_dir / name
        if not path.exists():
            return "Worktree not found"

        try:
            result = self._run_git(["status", "--porcelain"], cwd=path)
            return result.stdout
        except subprocess.CalledProcessError:
            return "Error getting status"

    def diff(self, name: str) -> str:
        """Diffs the worktree against HEAD."""
        path = self.worktrees_dir / name
        if not path.exists():
            return "Worktree not found"

        try:
            result = self._run_git(["diff", "HEAD"], cwd=path)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error running diff: {e.stderr}"

    def revert(self, name: str) -> bool:
        """Reverts all changes in a worktree."""
        path = self.worktrees_dir / name
        if not path.exists():
            return False

        try:
            self._run_git(["reset", "--hard", "HEAD"], cwd=path)
            self._run_git(["clean", "-fd"], cwd=path)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error reverting worktree: {e.stderr}")
            raise e

    def merge(self, name: str) -> str:
        """Merges the worktree branch into the current (main) branch."""
        # 1. Get branch info from listing
        worktrees = self.list_worktrees()
        target = next((w for w in worktrees if w.get("name") == name), None)
        if not target:
            raise ValueError(f"Worktree {name} not found.")

        branch_ref = target.get("branch", "")
        if not branch_ref:
             raise ValueError(f"Could not determine branch for worktree {name}")

        branch_name = branch_ref.replace("refs/heads/", "")

        # 2. Check for uncommitted changes in worktree
        path = self.worktrees_dir / name
        status = self.get_status(name)
        if status.strip():
             # Auto-commit
             self._run_git(["add", "."], cwd=path)
             self._run_git(["commit", "-m", f"Autocommit: Worktree merge for {name}"], cwd=path)

        # 3. Merge
        # We assume we are running this from the main repo context (which is self.project_dir)
        # But we need to make sure we are on the main branch?
        # Typically worktree management implies we are in the 'main' worktree or repo root.

        try:
            res = self._run_git(["merge", "--no-ff", branch_name])
            return res.stdout
        except subprocess.CalledProcessError as e:
            # Abort merge on failure to leave clean state
            self._run_git(["merge", "--abort"], check=False)
            raise e
