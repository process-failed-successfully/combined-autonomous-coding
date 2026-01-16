import re
import subprocess

def is_safe_git_ref(ref: str) -> bool:
    """
    Validates that a git reference name is safe to use in commands.
    A safe ref should not start with a '-' and should not contain characters
    that could be interpreted as command-line options or shell metacharacters.
    It also uses 'git check-ref-format' for a more robust check.
    """
    if not ref:
        return False
    # Rule 1: Must not start with a dash.
    if ref.startswith('-'):
        return False
    # Rule 2: Use git's own check for ref format. This is the most reliable way.
    # It checks for many unsafe patterns, like '..', '@{', '\\', etc.
    try:
        # We use --allow-onelevel because branch names like 'fix' are valid
        # although not recommended. In our context, we should allow them.
        subprocess.run(
            ['git', 'check-ref-format', '--allow-onelevel', ref],
            check=True, capture_output=True, text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If git check-ref-format fails, it's not a valid/safe ref.
        # FileNotFoundError would happen if git is not installed.
        return False
    except Exception:
        # Catch any other unexpected errors
        return False
