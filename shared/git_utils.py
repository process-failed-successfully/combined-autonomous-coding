"""
Git Utilities
=============

Functions for managing git state and ensuring safe branching for agents.
"""

import re


def is_safe_git_ref(ref: str) -> bool:
    """
    Validates if a git reference name is safe to use in commands.
    - Disallows refs starting with '-' to prevent option injection.
    - Disallows refs containing characters that might be interpreted by the shell.
    """
    if not ref:
        return False
    # Prevent option injection
    if ref.startswith("-"):
        return False
    # Disallow characters that could be used for command injection or have special
    # meaning in shells. This is a conservative list.
    # \t, \n, ;, &, |, `, $, (, ), <, >
    if re.search(r"[\t\n;&|`$()<>]", ref):
        return False
    return True
