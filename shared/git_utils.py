"""
Git Security Utilities
======================

Functions for ensuring git commands and references are safe.
"""
import re

def is_safe_git_ref(ref: str) -> bool:
    """
    Validates that a git reference is safe to use in commands.
    A safe ref is a commit hash (SHA-1 or SHA-256), a common branch or tag name, or a Run ID.
    It explicitly disallows refs that start with a dash '-' to prevent argument injection.
    """
    if not ref or not isinstance(ref, str):
        return False

    # Disallow refs starting with '-' to prevent argument injection
    if ref.startswith("-"):
        return False

    # Allow standard git commit hashes (4-64 hex chars)
    # Allow Run IDs (e.g., run-12345-abcdef)
    # Allow common branch/tag names (e.g., main, feat/foo, v1.2.3)
    # This is a bit lenient but covers most common cases. The key is preventing argument injection.
    safe_pattern = r"^[a-zA-Z0-9_./-]{1,100}$"

    return bool(re.match(safe_pattern, ref))
