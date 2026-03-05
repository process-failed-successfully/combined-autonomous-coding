import subprocess
from pathlib import Path
from typing import List, Dict
import logging


logger = logging.getLogger(__name__)


class BranchLabManager:
    """Manages Git branches."""
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def _run_git(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Helper to run git commands."""
        return subprocess.run(
            ["git", "-C", str(self.project_dir)] + cmd,
            capture_output=True,
            text=True,
            check=True
        )

    def get_all_branches(self) -> List[Dict[str, str]]:
        """Returns a list of all branches with metadata."""
        branches = []
        try:
            # 1. Get merged branches to main or master
            merged_branches = set()
            main_branch = self._get_main_branch()

            if main_branch:
                try:
                    merged_output = self._run_git(["branch", "--merged", main_branch]).stdout
                    for line in merged_output.splitlines():
                        branch_name = line.strip().lstrip("* ")
                        merged_branches.add(branch_name)
                except subprocess.CalledProcessError:
                    pass

            # 2. Get all branches with metadata
            # Format: refname:short|authorname|committerdate:short|subject|refname
            fmt = "%(refname:short)|%(authorname)|%(committerdate:short)|%(subject)|%(refname)"
            output = self._run_git(["for-each-ref", f"--format={fmt}", "refs/heads/", "refs/remotes/"]).stdout

            for line in output.splitlines():
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) >= 5:
                    name = parts[0]
                    author = parts[1]
                    date = parts[2]
                    message = parts[3]
                    ref = parts[4]

                    is_remote = ref.startswith("refs/remotes/")
                    # Remote branch names usually have origin/name, checking merged status might be tricky.
                    # We'll stick to simple check for local branches.
                    is_merged = "Yes" if not is_remote and name in merged_branches else "No"
                    if is_remote and name.replace("origin/", "") in merged_branches:
                        is_merged = "Yes"

                    branches.append({
                        "name": name,
                        "type": "Remote" if is_remote else "Local",
                        "author": author,
                        "date": date,
                        "message": message,
                        "merged": is_merged
                    })
            return branches
        except Exception as e:
            logger.error(f"Error listing branches: {e}")
            return []

    def _get_main_branch(self) -> str:
        """Try to guess the main branch."""
        for name in ["main", "master"]:
            try:
                self._run_git(["rev-parse", "--verify", name])
                return name
            except subprocess.CalledProcessError:
                continue
        return ""

    def checkout(self, branch_name: str) -> bool:
        """Checkout a branch."""
        try:
            self._run_git(["checkout", branch_name])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Checkout error: {e.stderr}")
            return False

    def delete_branches(self, branch_names: List[str], force: bool = False) -> Dict[str, bool]:
        """Deletes branches. Returns a dictionary of branch_name to success boolean."""
        results = {}
        for name in branch_names:
            try:
                cmd = ["branch", "-D" if force else "-d", name]
                # If it's remote, deleting is different: git push origin --delete name
                if name.startswith("origin/"):
                    remote_name = name.replace("origin/", "", 1)
                    cmd = ["push", "origin", "--delete", remote_name]

                self._run_git(cmd)
                results[name] = True
            except subprocess.CalledProcessError as e:
                logger.error(f"Delete error for {name}: {e.stderr}")
                results[name] = False
        return results


def run_branch_lab_logic(args) -> bool:
    """CLI logic for Branch Lab."""
    # Just a placeholder for CLI logic if needed
    print("Branch Lab CLI not implemented yet. Use 'main.py branch-lab tui'.")
    return True
