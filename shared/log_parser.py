
import re
from typing import List, Dict, Union

# Enhanced regex to capture the full, multi-line content of each section
REPLAY_STEP_PATTERN = re.compile(
    r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (INFO|ERROR) - (Thinking|Tool Call|Tool Output|User Input|Agent Message):",
    re.MULTILINE,
)

def parse_log_file(log_content: str) -> List[Dict[str, Union[str, int]]]:
    """
    Parses the content of an agent's log file into a structured list of replay steps.

    Each step is a dictionary containing the timestamp, type, and content of the event.
    The content is cleaned of ANSI escape codes for better readability.

    Args:
        log_content: The string content of the log file.

    Returns:
        A list of dictionaries, where each dictionary represents a single step in the agent's process.
    """
    steps = []
    # ANSI escape code pattern
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

    # Find all matches using the comprehensive pattern
    matches = list(REPLAY_STEP_PATTERN.finditer(log_content))

    for i, match in enumerate(matches):
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(log_content)

        timestamp, level, step_type = match.groups()
        content = log_content[start_pos:end_pos]

        # Clean the content from ANSI escape codes and strip leading/trailing whitespace
        cleaned_content = ansi_escape.sub('', content).strip()

        steps.append({
            "step": i + 1,
            "timestamp": timestamp,
            "level": level,
            "type": step_type,
            "content": cleaned_content,
        })

    return steps
