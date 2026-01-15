import re


def is_safe_git_ref(ref: str) -> bool:
    """
    Validates that a git reference is safe to use in commands.

    Args:
        ref: The git reference to validate.

    Returns:
        True if the reference is safe, False otherwise.
    """
    if not ref:
        return False
    # Check for leading hyphens
    if ref.startswith("-"):
        return False
    # Check for characters that could be used for command injection
    if re.search(r"[;\|&`\(\)\$\<\>\*!]", ref):
        return False
    return True
