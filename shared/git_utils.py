import re

def is_safe_git_ref(ref: str) -> bool:
    """
    Validates a git reference to prevent command injection.

    Allows standard branch and tag names, commit hashes, and relative refs like HEAD~1.
    Prevents refs that start with a dash or contain characters that could be used for
    command injection.
    """
    if not ref:
        return False
    # Regex to allow alphanumeric characters, slashes, dots, dashes, underscores, and tildes.
    # It must not start with a dash.
    return re.match(r"^[a-zA-Z0-9_][a-zA-Z0-9_./~-]*$", ref) is not None
