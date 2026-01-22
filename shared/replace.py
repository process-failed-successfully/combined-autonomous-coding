import re
import difflib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from shared.search import search_codebase

def replace_in_codebase(
    project_dir: Path,
    pattern: str,
    replacement: str,
    file_pattern: Optional[str] = None,
    case_sensitive: bool = False,
    is_regex: bool = False,
    dry_run: bool = False
) -> Dict:
    """
    Performs search and replace in the codebase.

    Args:
        project_dir: The root directory.
        pattern: The pattern to search for.
        replacement: The string to replace it with.
        file_pattern: Glob pattern to filter files.
        case_sensitive: Whether search is case sensitive.
        is_regex: Whether the pattern is a regex.
        dry_run: If True, do not modify files, just return diffs.

    Returns:
        A dictionary with summary of changes.
    """
    project_dir = project_dir.resolve()

    # 1. Find candidate files using search_codebase
    # We use search_codebase to leverage git ignore and glob logic.
    # It returns matches, but we only care about the unique files.
    # Note: search_codebase creates a regex internally if !is_regex,
    # but we need our own regex for replacement to ensure consistency.

    matches = search_codebase(
        project_dir=project_dir,
        pattern=pattern,
        file_pattern=file_pattern,
        case_sensitive=case_sensitive,
        is_regex=is_regex,
        context_lines=0,
        use_git_grep=True # Use fast path for finding files
    )

    unique_files = sorted(list(set(m['file'] for m in matches)))

    stats: Dict[str, Any] = {
        "files_matched": len(unique_files),
        "files_changed": 0,
        "replacements_count": 0,
        "diffs": {}
    }

    if not unique_files:
        return stats

    # Prepare regex for replacement
    flags = 0 if case_sensitive else re.IGNORECASE
    if not is_regex:
        # If not regex, we match literal string.
        # For re.sub, we escape the pattern.
        regex_pattern = re.escape(pattern)
    else:
        regex_pattern = pattern

    try:
        compiled_regex = re.compile(regex_pattern, flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")

    for rel_path in unique_files:
        file_path = project_dir / rel_path

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
        except Exception:
            # Skip unreadable
            continue

        # Apply replacement
        # We use re.sub for both regex and non-regex (escaped) to handle case insensitivity flags easily
        # However, for non-regex, we must be careful about the replacement string containing backslashes
        # which re.sub interprets as escapes/groups.

        final_replacement = replacement
        if not is_regex:
            # Escape backslashes in replacement if treating as literal string replacement via re.sub
            # Actually, standard str.replace doesn't support case insensitivity easily.
            # So re.sub is better, but we must escape the replacement string so it's treated literally.
            final_replacement = replacement.replace('\\', '\\\\')

        new_content, count = compiled_regex.subn(final_replacement, original_content)

        if count > 0 and new_content != original_content:
            stats["replacements_count"] += count
            stats["files_changed"] += 1

            # Generate Diff
            diff = list(difflib.unified_diff(
                original_content.splitlines(),
                new_content.splitlines(),
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
                lineterm=""
            ))

            # Format diff as string
            diff_text = "\n".join(diff)
            stats["diffs"][str(rel_path)] = diff_text

            if not dry_run:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                except Exception as e:
                    print(f"Error writing to {rel_path}: {e}")

    return stats
