import os
import shutil
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Union, Any

def search_codebase(
    project_dir: Path,
    pattern: str,
    file_pattern: Optional[str] = None,
    case_sensitive: bool = False,
    is_regex: bool = False,
    context_lines: int = 0,
    use_git_grep: bool = True
) -> List[Dict]:
    """
    Searches the project directory for a pattern.

    Args:
        project_dir: The root directory to scan.
        pattern: The text or regex pattern to search for.
        file_pattern: Glob pattern to filter files (e.g., "*.py").
        case_sensitive: Whether the search is case sensitive.
        is_regex: Whether the pattern is a regex.
        context_lines: Number of lines of context to include.
        use_git_grep: Whether to attempt using 'git grep' for performance.

    Returns:
        A list of dictionaries containing: file, line, content, context_before, context_after.
    """
    project_dir = project_dir.resolve()

    # Pre-compile regex if using python fallback or if we need to highlight/validate
    flags = 0 if case_sensitive else re.IGNORECASE
    if not is_regex:
        regex_pattern = re.escape(pattern)
    else:
        regex_pattern = pattern

    try:
        compiled_regex = re.compile(regex_pattern, flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {e}")

    git_path = shutil.which("git")
    is_git_repo = (project_dir / ".git").is_dir()

    if use_git_grep and git_path and is_git_repo:
        try:
            return _search_with_git_grep(
                project_dir, pattern, file_pattern, case_sensitive, is_regex, context_lines, git_path
            )
        except Exception:
            # Fallback to python scan if git grep fails
            pass

    return _search_with_python(
        project_dir, compiled_regex, file_pattern, context_lines, is_git_repo, git_path
    )


def _search_with_git_grep(
    project_dir: Path,
    pattern: str,
    file_pattern: Optional[str],
    case_sensitive: bool,
    is_regex: bool,
    context_lines: int,
    git_path: str
) -> List[Dict[str, Any]]:
    """Uses git grep to find matches."""
    cmd = [git_path, "-C", str(project_dir), "grep", "-n", "-I"]

    if not case_sensitive:
        cmd.append("-i")

    if not is_regex:
        cmd.append("-F")
    else:
        cmd.append("-E")

    if context_lines > 0:
        cmd.extend(["-C", str(context_lines)])

    # Pattern must come before pathspec
    cmd.append(pattern)

    # Add pathspec if provided
    if file_pattern:
        cmd.append("--")
        cmd.append(file_pattern)

    # Use subprocess to run
    # check=False because exit code 1 means no matches, which is not an exception for us
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )

    if result.returncode > 1:
        # Error in git grep arguments or execution
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)

    if not result.stdout:
        return []

    return _parse_git_grep_output(result.stdout, context_lines)


def _parse_git_grep_output(output: str, context_lines: int) -> List[Dict]:
    """Parses git grep output, potentially with context."""
    results = []
    lines = output.splitlines()

    current_match = None

    # Helper to finalize a match
    def finalize_match(match):
        if match:
            results.append(match)

    # If no context, formatting is simple: file:line:content
    if context_lines == 0:
        for line in lines:
            try:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    results.append({
                        "file": parts[0],
                        "line": int(parts[1]),
                        "content": parts[2],
                        "context_before": [],
                        "context_after": []
                    })
            except ValueError:
                continue
        return results

    # With context, lines look like:
    # file-4-context
    # file:5:match
    # file-6-context
    # --

    # We need to statefully parse this.
    # We will group by file logic effectively

    # Actually, simpler approach:
    # Identify lines that are matches (:separator) vs context (-separator).
    # Since filename can contain anything, parsing is tricky if we don't know the filename.
    # But git grep usually output is unambiguous if we look for the separator.
    # However, filename:line:content vs filename-line-content.

    # We will accumulate context lines. When we hit a match, we assign context_before.
    # Then we accumulate context_after until we hit another match or '--' or end of block.

    # This is slightly complex because multiple matches can overlap in context.
    # git grep merges them.
    # e.g. match at 5, match at 7, context 1.
    # 4-ctx
    # 5:match
    # 6:ctx (also ctx for 7)
    # 7:match
    # 8-ctx

    # Let's do a robust parse.

    # Group lines by file? No, git grep output is sorted by file.

    buffer_lines: List[Dict[str, Any]] = [] # list of (line_num, content, is_match, file)

    for line in lines:
        if line == "--":
            # Separator between disjoint matches
            _process_buffer(buffer_lines, results)
            buffer_lines = []
            continue

        # Try to parse line
        # We need to find the first separator which is either - or : following a number
        # Regex is best here.
        # ^(?P<file>.*)(?P<sep>[-:])(?P<line>\d+)(?P<sep2>[-:])(?P<content>.*)$
        # Wait, git grep output format is: filename:line:content OR filename-line-content
        # Note: filename can contain dashes.
        # But standard git grep separates filename and line with : or -

        # Heuristic: split by the first occurrence of ":\d+:" or "-\d+-"
        # Actually it's ":<digits>:" or "-<digits>-"

        match = re.match(r"^(.*?)([:-])(\d+)([:-])(.*)$", line)
        if match:
            f_path = match.group(1)
            sep1 = match.group(2)
            l_num = int(match.group(3))
            sep2 = match.group(4)
            content = match.group(5)

            # sep1 and sep2 should match for standard grep output,
            # BUT git grep uses ':' for match and '-' for context.
            # actually format is:
            # Match: file:line:content
            # Context: file-line-content

            is_match = (sep1 == ':' and sep2 == ':')
            # Context lines use '-' for both separators usually.

            buffer_lines.append({
                "file": f_path,
                "line": l_num,
                "content": content,
                "is_match": is_match
            })
        else:
            # Could be binary file match or something else
            pass

    _process_buffer(buffer_lines, results)

    return results

def _process_buffer(buffer: List[Dict], results: List[Dict]):
    """
    Process a block of lines (from git grep) to extract matches and assign context.
    Handles overlapping contexts.
    """
    if not buffer:
        return

    # Identify indices of matches
    match_indices = [i for i, x in enumerate(buffer) if x['is_match']]

    for i in match_indices:
        item = buffer[i]

        # Context before: everything in buffer before i, belonging to same file
        # Check file consistency (should be same file in a block usually, but safely check)
        c_before: List[str] = []
        for j in range(i - 1, -1, -1):
            if buffer[j]['file'] != item['file']:
                break
            # If we hit another match, do we stop?
            # Git grep merges output.
            # If line j is a match, it is technically context for line i as well if it's close enough.
            # But usually we want "context" to be non-matching lines?
            # Actually, standard grep display shows matching lines as context for other matches if they overlap.
            # For this tool, let's just include the raw line content.
            c_before.insert(0, f"{buffer[j]['line']}: {buffer[j]['content']}")

        # Context after: everything in buffer after i
        c_after = []
        for j in range(i + 1, len(buffer)):
            if buffer[j]['file'] != item['file']:
                break
            c_after.append(f"{buffer[j]['line']}: {buffer[j]['content']}")

            # Optimization: if we hit another match, and we want to avoid duplication in "context after",
            # we might want to stop?
            # No, let's just dump the block.
            # However, simpler: just take N lines before and N lines after if we knew N.
            # But here we don't know N easily from the buffer alone (it might be truncated at start/end of file).
            # The buffer contains EXACTLY what git grep outputted for this block.
            # So for a match at index i, everything else in the buffer IS the context that git grep decided to show.
            # But we must assign it correctly.

            # Refined logic:
            # If I have:
            # 1-ctx
            # 2:match1
            # 3:match2
            # 4-ctx

            # match1 has context_before=[1], context_after=[3, 4] ?
            # match2 has context_before=[1, 2], context_after=[4] ?
            # This seems redundant but correct for independent match objects.

        results.append({
            "file": item['file'],
            "line": item['line'],
            "content": item['content'],
            "context_before": [f"{x['line']}: {x['content']}" for x in buffer if x['line'] < item['line'] and x['file'] == item['file']],
            "context_after": [f"{x['line']}: {x['content']}" for x in buffer if x['line'] > item['line'] and x['file'] == item['file']]
        })

        # Wait, the simple logic above includes ALL lines in the buffer for the same file.
        # If there are multiple matches in one block, they share context.
        # This is fine.


def _search_with_python(
    project_dir: Path,
    regex: re.Pattern[str],
    file_pattern: Optional[str],
    context_lines: int,
    is_git_repo: bool,
    git_path: str
) -> List[Dict[str, Any]]:
    """Fallback python scanning."""
    results = []

    # Helper to check ignores
    def is_ignored(path: Path) -> bool:
        if is_git_repo and git_path:
            try:
                # Use --quiet. Exit code 0 = ignored, 1 = not ignored.
                res = subprocess.run(
                    [git_path, "-C", str(project_dir), "check-ignore", "-q", str(path)],
                    capture_output=True
                )
                return res.returncode == 0
            except Exception:
                return False
        return False

    # Helper for glob matching
    import fnmatch
    def matches_file_pattern(filename: str) -> bool:
        if not file_pattern:
            return True
        return fnmatch.fnmatch(filename, file_pattern)

    ignore_dirs = {'.git', '__pycache__', '.venv', 'node_modules', 'dist', 'build', '.agent_trash', '.agent_archives'}

    for root, dirs, files in os.walk(project_dir):
        root_path = Path(root)

        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not is_ignored(root_path / d)]

        for file in files:
            if not matches_file_pattern(file):
                continue

            file_path = root_path / file

            if is_ignored(file_path):
                continue

            try:
                # Read all lines to handle context
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_lines = f.readlines()

                for i, line in enumerate(file_lines):
                    # Strip newline for matching/display
                    clean_line = line.rstrip('\n')

                    if regex.search(clean_line):
                        # Found match
                        line_num = i + 1

                        c_before = []
                        if context_lines > 0:
                            start = max(0, i - context_lines)
                            c_before = [l.rstrip('\n') for l in file_lines[start:i]]

                        c_after = []
                        if context_lines > 0:
                            end = min(len(file_lines), i + 1 + context_lines)
                            c_after = [l.rstrip('\n') for l in file_lines[i+1:end]]

                        results.append({
                            "file": str(file_path.relative_to(project_dir)),
                            "line": line_num,
                            "content": clean_line,
                            "context_before": c_before,
                            "context_after": c_after
                        })
            except Exception:
                # Skip unreadable files
                continue

    return results
