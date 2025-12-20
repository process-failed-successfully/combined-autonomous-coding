#!/usr/bin/env python3
import sys
import subprocess
import os

# Protected branches that cannot be pushed to
PROTECTED_BRANCHES = ["main", "master"]


def get_current_branch():
    try:
        result = subprocess.run(
            ["git.real", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception:
        return None


def main():
    args = sys.argv[1:]

    # Check if this is a push command
    if args and args[0] == "push":
        # 1. Check current branch if no explicit branch is provided
        current_branch = get_current_branch()

        # We block if current branch is protected and we are doing a simple push
        # or if any argument matches a protected branch

        is_blocked = False
        blocked_reason = ""

        # Check arguments for branch names
        for arg in args:
            if arg in PROTECTED_BRANCHES:
                is_blocked = True
                blocked_reason = f"Explicitly pushing to protected branch '{arg}' is forbidden."
                break

        # If no explicit branch in args, check current branch
        if not is_blocked and current_branch in PROTECTED_BRANCHES:
            # Check if args contains origin or other remotes without branch names
            # git push origin
            # git push
            # If it's a simple push and we are on main, block it.
            # We assume if no branch-like arg is found, it's pushing current.
            has_branch_arg = False
            for arg in args[1:]:
                if not arg.startswith("-") and arg != "origin":
                    # This might be a branch name
                    has_branch_arg = True
                    break

            if not has_branch_arg:
                is_blocked = True
                blocked_reason = f"Attempting to push from protected branch '{current_branch}' is forbidden."

        if is_blocked:
            print(f"FAILED: {blocked_reason}", file=sys.stderr)
            print("Agents are not allowed to push to 'main' or 'master' branches.", file=sys.stderr)
            sys.exit(1)

    # Execute real git
    # We expect 'git.real' to be the original git binary
    cmd = ["git.real"] + args
    try:
        # Use os.execvp to replace the current process
        os.execvp("git.real", cmd)
    except FileNotFoundError:
        # Fallback if git.real is not set up yet (for local testing)
        # In this case we just use the system 'git' but avoid infinite recursion
        if os.environ.get("GIT_WRAPPER_TESTING"):
            print("DEBUG: Executing real git (mocked)", file=sys.stderr)
            sys.exit(0)

        # If we are not in testing mode and git.real is missing, it's a configuration error
        print("Error: git.real not found. Git wrapper is not correctly installed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
