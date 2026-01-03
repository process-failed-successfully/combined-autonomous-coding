import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class WorktreeManager:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.worktrees_dir = repo_path / ".sprint_workspaces"
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)
        # Check if git is available
        try:
            subprocess.run(["git", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.git_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.git_available = False
            logger.warning("Git not available. Sprint Isolation will be disabled (risky).")

    def _run_git(self, args: list[str], cwd: Optional[Path] = None) -> None:
        if not cwd:
            cwd = self.repo_path
        
        # Suppress output unless error
        subprocess.run(
            ["git"] + args,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def create_worktree(self, task_id: str) -> Optional[Path]:
        """creates a new worktree for the task."""
        if not self.git_available:
            return self.repo_path

        worktree_path = self.worktrees_dir / task_id
        branch_name = f"sprint/task-{task_id}"

        if worktree_path.exists():
            logger.warning(f"Worktree path {worktree_path} already exists. Cleaning up first.")
            self.cleanup_worktree(task_id)

        try:
            # Create a new branch and checkout in new worktree
            # We explicitly base it on HEAD of the main repo
            logger.info(f"Creating worktree for {task_id} at {worktree_path}")
            self._run_git(["worktree", "add", "-b", branch_name, str(worktree_path), "HEAD"])
            return worktree_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree: {e.stderr}")
            return None

    def merge_worktree(self, task_id: str) -> bool:
        """Merges the worktree branch back into the main branch."""
        if not self.git_available:
            return True # Assume direct edits on main repo

        branch_name = f"sprint/task-{task_id}"
        
        try:
            # We merge into the CURRENT main branch (where the process is running)
            # This ensures subsequent tasks see the changes.
            # Note: The main repo might have moved forward if other tasks merged.
            
            logger.info(f"Merging changes from {branch_name}...")
            
            # 1. Fetch/Update view of branches? Worktrees share refs, so no fetch needed.
            
            # 2. Merge
            # We are in the main repo.
            self._run_git(["merge", "--no-ff", branch_name, "-m", f"Merge task {task_id}"])
            
            logger.info(f"Successfully merged {branch_name}.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to merge worktree {task_id}: {e.stderr}")
            # TODO: Handle conflicts?
            # For now, we fail the task or leave it for manual resolution?
            # If merge fails, future tasks depending on this might fail or miss code.
            return False

    def rescue_worktree(self, task_id: str) -> bool:
        """Commits any pending changes in the worktree to save progress."""
        if not self.git_available:
            return False

        worktree_path = self.worktrees_dir / task_id
        if not worktree_path.exists():
            return False

        try:
            logger.info(f"Rescuing worktree for {task_id} (Committing WIP)...")
            # 1. Add all changes
            self._run_git(["add", "."], cwd=worktree_path)
            
            # 2. Commit (allow empty if nothing to commit)
            # We use allow-empty just in case, or ignore error if nothing to commit
            try:
                self._run_git(["commit", "-m", f"WIP: Saved progress for task {task_id} on interrupt"], cwd=worktree_path)
            except subprocess.CalledProcessError:
                # Likely nothing to commit, which is fine
                pass
                
            return True
        except Exception as e:
            logger.error(f"Failed to rescue worktree {task_id}: {e}")
            return False

    def cleanup_worktree(self, task_id: str, delete_branch: bool = True) -> None:
        """Removes the worktree. Optionally deletes the branch."""
        if not self.git_available:
            return

        worktree_path = self.worktrees_dir / task_id
        branch_name = f"sprint/task-{task_id}"

        # Delete worktree
        if worktree_path.exists():
             try:
                 # 'git worktree remove' is cleaner than rm -rf
                 self._run_git(["worktree", "remove", "--force", str(worktree_path)])
             except subprocess.CalledProcessError:
                 # Fallback
                 shutil.rmtree(worktree_path, ignore_errors=True)
                 # Prune to clean up git internals
                 try:
                    self._run_git(["worktree", "prune"])
                 except: 
                    pass

        # Delete branch
        if delete_branch:
            try:
                self._run_git(["branch", "-D", branch_name])
            except Exception:
                pass
