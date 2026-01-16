import shutil
import subprocess
import sys
from pathlib import Path

from shared.git_utils import is_safe_git_ref, find_commit_by_run_id


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

    # --- Target Resolution & Validation ---
    original_target = target
    commit_to_pick = None

    # First, try to treat the target as a git reference
    if is_safe_git_ref(original_target):
        try:
            # Use '--' to protect against targets starting with a dash
            check_commit_result = subprocess.run(
                [git_path, "-C", str(project_dir), "cat-file", "-t", "--", original_target],
                capture_output=True, text=True
            )
            if check_commit_result.returncode == 0 and check_commit_result.stdout.strip() == "commit":
                commit_to_pick = original_target
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # Not a valid git object, so we'll try it as a run ID

    # If it's not a direct commit ref, assume it's a Run ID
    if commit_to_pick is None:
        print(f"'{original_target}' is not a known git commit. Assuming it is a Run ID and searching history...")
        resolved_hash = find_commit_by_run_id(project_dir, git_path, original_target)

        if resolved_hash:
            # We found a commit. We MUST validate this hash before using it.
            if not is_safe_git_ref(resolved_hash):
                print(
                    f"❌ Error: The commit hash '{resolved_hash}' found for Run ID '{original_target}' is not a safe git reference.",
                    file=sys.stderr)
                sys.exit(1)
            print(f"✅ Found commit '{resolved_hash[:7]}' associated with Run ID '{original_target}'.")
            commit_to_pick = resolved_hash
        else:
            print(f"❌ Error: Could not find a git commit for target '{original_target}'.", file=sys.stderr)
            print("Please provide a valid commit hash or a Run ID from the agent's history.", file=sys.stderr)
            sys.exit(1)

    # Final check
    if not commit_to_pick:
        print(f"❌ Error: Could not resolve '{original_target}' to a valid commit.", file=sys.stderr)
        sys.exit(1)

    # --- Execute Cherry-Pick ---
    print(f"--- Applying commit {commit_to_pick[:7]} onto the current branch ---")
    try:
        # Use --no-commit to allow the user to inspect the changes before committing
        # Use '--' to ensure the target is treated as a positional argument, not an option
        cmd = [git_path, "-C", str(project_dir), "cherry-pick", "--no-commit", "--", commit_to_pick]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout)
            print(f"\n✅ Successfully cherry-picked commit {commit_to_pick[:7]}.")
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
