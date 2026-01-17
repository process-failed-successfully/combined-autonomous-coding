import shutil
import subprocess
import sys
from pathlib import Path

def _find_commit_by_run_id(project_dir: Path, git_path: str, run_id: str) -> str | None:
    """Searches the git log for a commit associated with a Run ID."""
    try:
        # Search the entire commit history for the Run ID in the message body
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "log", "--all", f"--grep=Run ID: {run_id}", "--format=%H"],
            capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            # Return the first commit hash found
            return result.stdout.strip().split('\n')[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return None

def run_cherry_pick(args):
    """Applies the changes from a specific commit onto the current branch."""
    project_dir = args.project_dir.resolve()
    target = args.target

    # --- Pre-flight checks ---
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

    git_dir = project_dir / ".git"
    if not git_dir.exists() or not git_dir.is_dir():
        print("❌ Error: Not a git repository. Cannot cherry-pick.", file=sys.stderr)
        sys.exit(1)

    # Validate target format to prevent injection
    from shared.utils import is_safe_git_ref
    if not is_safe_git_ref(target):
        print(f"❌ Error: Invalid git reference '{target}'.", file=sys.stderr)
        sys.exit(1)

    # --- Target Resolution: Commit Hash vs. Run ID ---
    original_target = target
    # First, check if the target is a valid git object (commit, tag, etc.)
    is_git_ref = False
    try:
        check_commit_result = subprocess.run(
            [git_path, "-C", str(project_dir), "cat-file", "-t", target],
            capture_output=True, text=True
        )
        if check_commit_result.returncode == 0 and check_commit_result.stdout.strip() == "commit":
            is_git_ref = True
    except Exception:
        pass  # Ignore errors, we'll handle the 'not found' case below

    if not is_git_ref:
        print(f"'{target}' is not a known git commit. Assuming it is a Run ID and searching history...")
        commit_hash = _find_commit_by_run_id(project_dir, git_path, target)
        if commit_hash:
            print(f"✅ Found commit '{commit_hash[:7]}' associated with Run ID '{target}'.")
            target = commit_hash
            if not is_safe_git_ref(target):
                print(f"❌ Error: Resolved commit hash '{target}' is invalid.", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"❌ Error: Could not find a git commit for target '{original_target}'.", file=sys.stderr)
            print("Please provide a valid commit hash or a Run ID from the agent's history.", file=sys.stderr)
            sys.exit(1)

    # --- Execute Cherry-Pick ---
    print(f"--- Applying commit {target[:7]} onto the current branch ---")
    try:
        # Use --no-commit to allow the user to inspect the changes before committing
        cmd = [git_path, "-C", str(project_dir), "cherry-pick", "--no-commit", "--", target]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout)
            print(f"\n✅ Successfully cherry-picked commit {target[:7]}.")
            sys.exit(0)
        else:
            print("❌ Error: Cherry-pick failed.", file=sys.stderr)
            print("This is likely due to a merge conflict.", file=sys.stderr)
            print("\n--- Git Output ---", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            print("------------------", file=sys.stderr)
            print("\nPlease resolve the conflicts in your editor and then run:", file=sys.stderr)
            print(f"  git cherry-pick --continue", file=sys.stderr)
            print("\nTo abort the cherry-pick and return to the previous state, run:", file=sys.stderr)
            print(f"  git cherry-pick --abort", file=sys.stderr)
            sys.exit(1)

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        stderr = getattr(e, 'stderr', str(e))
        if isinstance(stderr, bytes):
            stderr = stderr.decode().strip()
        print(f"❌ An unexpected error occurred: {stderr}", file=sys.stderr)
        sys.exit(1)
