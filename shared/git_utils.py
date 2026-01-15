import re
import sys

def is_safe_git_ref(ref: str) -> bool:
    """
    Validates a git reference to prevent command injection vulnerabilities.
    - Disallows refs starting with '-' to prevent option injection.
    - Disallows refs containing shell metacharacters.
    - Allows alphanumeric characters, slashes, dots, underscores, and hyphens.
    """
    if not isinstance(ref, str) or not ref:
        return False

    # Check for leading hyphen
    if ref.startswith("-"):
        return False

    # Allow only a restricted set of characters commonly found in git refs
    # (alphanumeric, underscore, hyphen, dot, slash, tilde)
    # This is a whitelist approach, which is generally safer.
    if not re.match(r"^[a-zA-Z0-9_./~-]+$", ref):
        return False

    return True

def validate_git_ref(ref: str, ref_name_for_error_message: str = "git reference"):
    """
    Validates a git reference and exits if it is unsafe.
    """
    if not is_safe_git_ref(ref):
        print(f"❌ Error: Invalid {ref_name_for_error_message} '{ref}'. The value contains unsafe characters or does not conform to expected format.", file=sys.stderr)
        sys.exit(1)
