import re
import sys

def is_safe_git_ref(ref: str) -> bool:
    """
    Validates a git reference to ensure it doesn't contain characters
    that could be used for command injection.
    """
    # According to git-check-ref-format, a valid ref should not:
    # 1. Start with '-'
    # 2. Contain '..'
    # 3. Contain ASCII control characters
    # 4. Contain shell special characters like ' ', ';', '|', '&&', '||', '>', '<'
    # We will be even stricter for safety.
    if ref.startswith("-"):
        return False

    # Allow alphanumeric, underscore, dash, dot, and forward slash
    # This is a restrictive regex for safety.
    if not re.match(r'^[a-zA-Z0-9_./-]+$', ref):
        return False

    return True

def validate_git_ref_or_exit(ref: str, ref_name: str = "reference"):
    """
    Validates a git reference using is_safe_git_ref and exits if it's unsafe.
    """
    if not is_safe_git_ref(ref):
        print(f"Error: Invalid or potentially unsafe git {ref_name} provided: '{ref}'", file=sys.stderr)
        sys.exit(1)
