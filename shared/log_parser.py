import re
from dataclasses import dataclass
from typing import List

@dataclass
class LogStep:
    """Represents a single step in the agent's execution, parsed from the log."""
    thought: str
    action: str

def parse_log_file(log_content: str) -> List[LogStep]:
    """
    Parses the full content of a log file into a list of structured LogStep objects.

    Args:
        log_content: A string containing the entire log file content.

    Returns:
        A list of LogStep objects, each representing a thought/action pair.
    """
    steps = []
    # Regex to find all thought and action blocks
    pattern = re.compile(
        r"(?s)(?:\d{2}:\d{2}:\d{2} - DEBUG - Sending Augmented Prompt:\n)(.*?)"
        r"(?=\d{2}:\d{2}:\d{2} - INFO - Sending prompt to Gemini...|$)"
    )
    matches = pattern.findall(log_content)
    for match in matches:
        parts = re.split(r"(?s)(---)", match)
        thought = parts[0].strip()
        action = "".join(parts[1:]).strip()
        steps.append(LogStep(thought=thought, action=action))

    return steps