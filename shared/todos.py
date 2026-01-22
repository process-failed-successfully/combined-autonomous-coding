import os
import shutil
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Set, Any, Pattern

DEFAULT_TAGS = ["TODO", "FIXME", "BUG", "HACK", "NOTE", "XXX"]

def scan_todos(
    project_dir: Path,
    tags: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
    use_git_grep: bool = True
) -> List[Dict[str, Any]]:
    """
    Scans the project directory for TODO comments.

    Args:
        project_dir: The root directory to scan.
        tags: List of tags to search for (e.g., ["TODO", "FIXME"]). Defaults to standard tags.
        exclude_paths: List of paths to exclude.
        use_git_grep: Whether to attempt using 'git grep' for performance.

    Returns:
        A list of dictionaries containing: file, line, tag, text.
    """
    project_dir = project_dir.resolve()
    tags = tags or DEFAULT_TAGS
    exclude_paths = exclude_paths or []

    # Construct regex pattern for tags
    # matches: TAG: text or TAG text
    # We want to capture the TAG and the rest of the line
    tags_pattern = "|".join(map(re.escape, tags))
    # Regex breakdown:
    # (?P<tag>...) : Named group for the tag
    # \s*: Optional whitespace/colon after tag
    # (?P<text>.*) : The rest of the comment
    # We rely on the caller/grep to find the line, this regex parses the line content
    line_parser = re.compile(rf"(?P<tag>{tags_pattern})[:\s]+(?P<text>.*)", re.IGNORECASE)

    results = []

    git_path = shutil.which("git")
    is_git_repo = (project_dir / ".git").is_dir()

    if use_git_grep and git_path and is_git_repo:
        try:
            results = _scan_with_git_grep(project_dir, tags, git_path, line_parser)
            return results
        except Exception:
            # Fallback to python scan if git grep fails
            pass

    results = _scan_with_python(project_dir, tags, exclude_paths, line_parser, is_git_repo, git_path)
    return results


def _scan_with_git_grep(
    project_dir: Path,
    tags: List[str],
    git_path: str,
    line_parser: Pattern[str]
) -> List[Dict[str, Any]]:
    """Uses git grep to find matches."""
    # Construct grep pattern: (TODO|FIXME|...)
    pattern = "|".join(tags)

    # -n: line numbers
    # -I: ignore binary
    # -E: extended regex
    # -i: case insensitive
    cmd = [git_path, "-C", str(project_dir), "grep", "-nIi", "-E", pattern]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )

    parsed_results = []
    if result.returncode not in [0, 1]:
        # Exit code 1 means no matches found, which is fine.
        # >1 means error.
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)

    if not result.stdout:
        return []

    for line in result.stdout.splitlines():
        # Output format: file:line:content
        # Note: path can contain colons, so we split only on the first two colons
        try:
            parts = line.split(":", 2)
            if len(parts) < 3:
                continue

            file_path, line_num, content = parts[0], parts[1], parts[2]

            # Parse the content to extract tag and text
            # We search for the tag in the content
            match = line_parser.search(content)
            if match:
                parsed_results.append({
                    "file": file_path,
                    "line": int(line_num),
                    "tag": match.group("tag").upper(), # Normalize tag
                    "text": match.group("text").strip(),
                    "raw_content": content.strip()
                })
            else:
                # Regex didn't match nicely (e.g. tag inside a word?),
                # but git grep found it. We'll do a best effort.
                # Find which tag matched
                found_tag = "TODO" # Default
                for tag in tags:
                    if tag in content:
                        found_tag = tag
                        break
                parsed_results.append({
                    "file": file_path,
                    "line": int(line_num),
                    "tag": found_tag,
                    "text": content.strip(),
                    "raw_content": content.strip()
                })

        except ValueError:
            continue

    return parsed_results


def _scan_with_python(
    project_dir: Path,
    tags: List[str],
    exclude_paths: List[str],
    line_parser: Pattern[str],
    is_git_repo: bool,
    git_path: Optional[str]
) -> List[Dict[str, Any]]:
    """Fallback python scanning."""
    parsed_results = []

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

    ignore_dirs = {'.git', '__pycache__', '.venv', 'node_modules', 'dist', 'build', '.agent_trash', '.agent_archives'}

    for root, dirs, files in os.walk(project_dir):
        root_path = Path(root)

        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not is_ignored(root_path / d)]

        for file in files:
            file_path = root_path / file

            # Skip excluded paths
            if any(str(file_path).startswith(str(project_dir / excl)) for excl in exclude_paths):
                continue

            if is_ignored(file_path):
                continue

            try:
                # Skip binary files check? Simple check for null byte
                # Reading line by line
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, 1):
                        # Quick check before regex
                        if any(tag in line for tag in tags):
                            match = line_parser.search(line)
                            if match:
                                parsed_results.append({
                                    "file": str(file_path.relative_to(project_dir)),
                                    "line": i,
                                    "tag": match.group("tag").upper(),
                                    "text": match.group("text").strip(),
                                    "raw_content": line.strip()
                                })
            except Exception:
                # Skip unreadable files
                continue

    return parsed_results


def get_todo_blame(project_dir: Path, file_path: str, line_num: int) -> Dict[str, str]:
    """
    Gets the blame information for a specific TODO.
    """
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        return {"author": "Unknown", "date": "Unknown", "commit": "Unknown"}

    try:
        # git blame -L line,line -p file
        # -p gives porcelain format which is easier to parse
        cmd = [git_path, "-C", str(project_dir), "blame", "-L", f"{line_num},{line_num}", "--porcelain", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        output = result.stdout.splitlines()
        # First line is hash
        commit_hash = output[0].split()[0]

        author = "Unknown"
        author_mail = ""
        date = "Unknown"

        for line in output:
            if line.startswith("author "):
                author = line[7:]
            elif line.startswith("author-mail "):
                author_mail = line[12:]
            elif line.startswith("author-time "):
                # Convert timestamp
                import datetime
                ts = int(line[12:])
                date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')

        return {
            "author": author,
            "date": date,
            "commit": commit_hash
        }

    except Exception:
        return {"author": "Unknown", "date": "Unknown", "commit": "Unknown"}
