import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class LogStep:
    """Represents a single step in the agent's execution, parsed from a log file."""
    timestamp: str
    thoughts: Optional[str]
    command: Optional[str]
    files: Optional[List[str]]
    stdout: Optional[str]
    diff: Optional[str]

def parse_log_file(run_id: str, project_dir: Path) -> List[LogStep]:
    """
    Parses an agent log file into a structured list of steps for replay.

    Args:
        run_id: The ID of the run to parse.
        project_dir: The root directory of the project.

    Returns:
        A list of LogStep objects representing the agent's execution flow.
    """
    repo_root = Path(__file__).parent.parent
    log_file_path = repo_root / f"agents/logs/{run_id}.log"

    if not log_file_path.exists():
        # As a fallback, check if the log is in the project directory's archives
        archive_log_path = project_dir / ".agent_archives"
        if archive_log_path.is_dir():
            for archive in sorted(archive_log_path.iterdir(), reverse=True):
                potential_log = archive / f"{run_id}.log"
                if potential_log.exists():
                    log_file_path = potential_log
                    break
        if not log_file_path.exists():
            raise FileNotFoundError(f"Log file for Run ID '{run_id}' not found.")

    try:
        log_content = log_file_path.read_text()
    except IOError as e:
        raise IOError(f"Error reading log file {log_file_path}: {e}") from e

    # This regex is designed to be non-greedy and handle multi-line content
    # It looks for a timestamp, then captures everything until the next timestamp or end of file
    log_entry_pattern = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - \w+ -.*?)(?=\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} -|$)",
        re.DOTALL
    )

    steps = []
    for match in log_entry_pattern.finditer(log_content):
        entry_text = match.group(1).strip()
        if not entry_text:
            continue

        # Extract timestamp from the first line
        first_line = entry_text.split('\n')[0]
        timestamp_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", first_line)
        timestamp = timestamp_match.group(1) if timestamp_match else "Unknown Time"

        # --- Use regex to find specific blocks within the entry ---
        thoughts = _extract_block(entry_text, "THOUGHTS")
        command = _extract_block(entry_text, "COMMAND")
        stdout = _extract_block(entry_text, "STDOUT")
        diff = _extract_block(entry_text, "DIFF")
        files_str = _extract_block(entry_text, "FILES")

        files = files_str.strip().split('\n') if files_str else None

        # Only create a step if there's meaningful content (command or thoughts)
        if command or thoughts:
            steps.append(LogStep(
                timestamp=timestamp,
                thoughts=thoughts,
                command=command,
                files=files,
                stdout=stdout,
                diff=diff,
            ))
    return steps


def _extract_block(text: str, block_name: str) -> Optional[str]:
    """
    Extracts a named block (e.g., THOUGHTS, COMMAND) from a log entry.
    A block starts with the block_name on a line by itself and ends
    before the next block name or the end of the entry.
    """
    # Pattern to find a block and capture its content until the next block or end of string.
    # It uses a positive lookahead to avoid consuming the next block's header.
    pattern = re.compile(
        rf"^{block_name}:\n(.*?)(?=\n(?:THOUGHTS|COMMAND|STDOUT|DIFF|FILES):|$)",
        re.DOTALL | re.MULTILINE
    )
    match = pattern.search(text)
    if match:
        # .strip() removes leading/trailing whitespace, including the final newline
        return match.group(1).strip()
    return None
