"""
Git Security Utilities
======================

Functions for ensuring that git-related inputs are safe and sanitized.
"""
import re

# A reasonably strict regex for git references.
# Allows:
# - Full SHA-1 hashes (40 characters).
# - Abbreviated SHA-1 hashes (7-40 characters).
# - Branch names (e.g., 'main', 'feat/new-feature', 'user/name/branch').
#   - Cannot start/end with '/', cannot contain '..', '\', or spaces.
# - Tags (e.g., 'v1.0.0').
# - HEAD, ORIG_HEAD, FETCH_HEAD, MERGE_HEAD.
# - Relative refs like HEAD~1, HEAD^2.
# - Custom 'run-' prefixes for agent-generated IDs.
# Does NOT allow shell metacharacters like ';', '|', '&', '$', '`', '(', ')'.
_SAFE_GIT_REF_PATTERN = re.compile(r"^(run-[\w-]+|[\w./@~^-]+)$")

def is_safe_git_ref(ref: str) -> bool:
    """
    Validates if a string is a safe git reference.

    This is a security measure to prevent command injection when using git
    commands with user-provided or agent-generated references. It checks against
    a regex that allows common git ref formats but disallows shell
    metacharacters.

    Args:
        ref: The git reference string to validate.

    Returns:
        True if the reference is considered safe, False otherwise.
    """
    if not ref or not isinstance(ref, str):
        return False

    # Basic length check to prevent extremely long inputs
    if len(ref) > 256:
        return False

    # Check against the regex
    if not _SAFE_GIT_REF_PATTERN.match(ref):
        return False

    # Additional paranoid checks
    if ".." in ref or "//" in ref:
        return False
    if ref.startswith("-"):
        # Disallow refs that could be misinterpreted as flags
        return False

    return True
