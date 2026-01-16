import re

def is_safe_git_ref(ref):
    """
    Validates a git reference to ensure it doesn't contain characters
    that could be used for command injection.
    """
    # Allow alphanumeric characters, slashes, dashes, underscores, and dots
    # Allows for branch names, commit hashes, HEAD, etc.
    if re.match(r'^[a-zA-Z0-9/._-]+$', ref):
        return True
    return False
