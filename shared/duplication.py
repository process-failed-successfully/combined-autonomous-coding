"""
Code Duplication Detector
=========================

Finds duplicate code blocks across the project using token-based analysis.
"""

import tokenize
import os
from pathlib import Path
from collections import defaultdict
import fnmatch
from typing import List, Dict, Any, Optional

# Token types to ignore for duplication purposes
IGNORED_TOKENS = {
    tokenize.COMMENT,
    tokenize.NL,
    tokenize.NEWLINE,
    tokenize.ENCODING,
    tokenize.ENDMARKER
}

def tokenize_file(filepath: Path):
    """
    Reads a file and returns a list of normalized tokens.
    Returns: list of (token_type, token_string, line_number)
    """
    tokens = []
    try:
        # Read as bytes for tokenize
        with open(filepath, 'rb') as f:
            for tok in tokenize.tokenize(f.readline):
                if tok.type in IGNORED_TOKENS:
                    continue

                # Normalize strings?
                # For strict CPD, we keep strings as is.
                # For "fuzzy" match, we might abstract them, but let's do exact match first.

                # We store (type, string, line)
                # For NAME tokens, we keep the string.
                tokens.append((tok.type, tok.string, tok.start[0]))

    except (tokenize.TokenError, IndentationError, IOError):
        # Skip files that can't be parsed
        pass

    return tokens

def find_duplicates(project_dir: Path, file_patterns: Optional[list[str]] = None, ignore_patterns: Optional[list[str]] = None, min_tokens: int = 50):
    """
    Scans the project for duplicate code.

    Args:
        project_dir: Root directory to scan.
        file_patterns: List of glob patterns to include (default: ['*.py']).
        ignore_patterns: List of glob patterns to exclude.
        min_tokens: Minimum sequence of tokens to count as duplicate.

    Returns:
        List of duplicate groups. Each group is a list of {'file': path, 'start_line': int, 'end_line': int}
    """
    project_dir = project_dir.resolve()

    # 1. Collect Files
    if not file_patterns:
        file_patterns = ["*.py"]

    all_files = []
    for root, dirs, filenames in os.walk(project_dir):
        # Ignore common hidden/build dirs
        if ".git" in dirs: dirs.remove(".git")
        if "__pycache__" in dirs: dirs.remove("__pycache__")
        if "node_modules" in dirs: dirs.remove("node_modules")
        if ".venv" in dirs: dirs.remove(".venv")

        for filename in filenames:
            path = Path(root) / filename
            rel_path = path.relative_to(project_dir)

            # Check inclusions
            if not any(fnmatch.fnmatch(str(rel_path), p) for p in file_patterns):
                continue

            # Check exclusions
            if ignore_patterns and any(fnmatch.fnmatch(str(rel_path), p) for p in ignore_patterns):
                continue

            all_files.append(path)

    # 2. Tokenize All Files
    # We flatten all tokens into a single list but keep track of their origin
    # global_tokens: list of int - used for matching (mapped IDs)
    # token_map: list of (file_path, line_number) - used for mapping back

    global_tokens = []
    token_map = []

    # Optimization: Map token tuples to integers to reduce memory and comparison cost
    token_to_id = {}
    next_id = 0

    for f in all_files:
        file_tokens = tokenize_file(f)
        if not file_tokens:
            continue

        for t_type, t_string, t_line in file_tokens:
            token_key = (t_type, t_string)
            if token_key not in token_to_id:
                token_to_id[token_key] = next_id
                next_id += 1

            global_tokens.append(token_to_id[token_key])
            token_map.append((f, t_line))

    if len(global_tokens) < min_tokens:
        return []

    # 3. Find Duplicates using Rolling Hash / Dictionary
    # Map: tuple(window_tokens) -> list of start_indices
    windows = defaultdict(list)

    # Pre-compute the first window
    current_window = tuple(global_tokens[:min_tokens])
    windows[current_window].append(0)

    for i in range(1, len(global_tokens) - min_tokens + 1):
        # Sliding window
        # Slicing a list of ints is faster than slicing a list of tuples
        current_window = tuple(global_tokens[i : i + min_tokens])
        windows[current_window].append(i)

    # 4. Process Matches (Diagonal Strategy)
    # We group matches by their offset (diagonal in the comparison matrix)
    # matches: dict mapping offset (j-i) to list of start indices i
    diagonals = defaultdict(list)

    for indices in windows.values():
        if len(indices) > 1:
            for k in range(len(indices)):
                for m in range(k + 1, len(indices)):
                    idx1 = indices[k]
                    idx2 = indices[m]
                    # Ensure idx1 < idx2
                    if idx1 > idx2:
                        idx1, idx2 = idx2, idx1

                    offset = idx2 - idx1
                    diagonals[offset].append(idx1)

    merged_duplicates = []

    for offset, starts in diagonals.items():
        if not starts:
            continue

        starts.sort()

        # Find runs of consecutive numbers
        current_start = starts[0]
        current_run_len = 1

        for k in range(1, len(starts)):
            if starts[k] == starts[k - 1] + 1:
                current_run_len += 1
            else:
                # End of run
                # Length of duplicate = current_run_len + min_tokens - 1
                final_len = current_run_len + min_tokens - 1
                merged_duplicates.append((current_start, current_start + offset, final_len))

                current_start = starts[k]
                current_run_len = 1

        # Append last run
        final_len = current_run_len + min_tokens - 1
        merged_duplicates.append((current_start, current_start + offset, final_len))

    # 5. Format Results
    results: List[Dict[str, Any]] = []
    for idx1, idx2, length in merged_duplicates:
        # Get file info
        file1, line1_start = token_map[idx1]
        file1, line1_end = token_map[idx1 + length - 1]

        file2, line2_start = token_map[idx2]
        file2, line2_end = token_map[idx2 + length - 1]

        results.append({
            "token_count": length,
            "locations": [
                {"file": str(file1.relative_to(project_dir)), "start_line": line1_start, "end_line": line1_end},
                {"file": str(file2.relative_to(project_dir)), "start_line": line2_start, "end_line": line2_end}
            ]
        })

    # Sort by token count descending (most severe first)
    results.sort(key=lambda x: x['token_count'], reverse=True)

    return results

def _run_duplication_logic(project_dir: Path, min_tokens: int = 50, files: Optional[str] = None, ignore: Optional[str] = None):
    """
    CLI Handler for duplication detection.
    """
    print(f"--- Code Duplication Detector: {project_dir.name} ---")
    print(f"Minimum Tokens: {min_tokens}")

    file_patterns = files.split(",") if files else ["*.py"]
    ignore_patterns = ignore.split(",") if ignore else []

    if file_patterns:
        print(f"Including: {', '.join(file_patterns)}")
    if ignore_patterns:
        print(f"Ignoring: {', '.join(ignore_patterns)}")

    print("\nScanning...")

    duplicates = find_duplicates(project_dir, file_patterns, ignore_patterns, min_tokens)

    if not duplicates:
        print("✅ No duplicates found.")
        return

    print(f"\n⚠️  Found {len(duplicates)} duplicate blocks:\n")

    # Filter out redundant sub-matches?
    # If A covers B, B might still be reported?
    # With diagonal merging, we shouldn't have sub-segments reported unless they are separate diagonals.
    # But internal repetition (A matches B, A matches C) will result in multiple pairs.

    for i, dup in enumerate(duplicates[:20]):  # Limit output
        count = dup['token_count']
        locs = dup['locations']

        print(f"[{i + 1}] {count} tokens duplicated:")
        for loc in locs:
            print(f"    📄 {loc['file']} : lines {loc['start_line']}-{loc['end_line']}")
        print("")

    if len(duplicates) > 20:
        print(f"... and {len(duplicates) - 20} more.")

    print(f"Total Duplicates: {len(duplicates)}")
