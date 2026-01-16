import re
from dataclasses import dataclass, field
from typing import List

@dataclass
class ReplayStep:
    """Represents a single step in an agent's execution replay."""
    thought: str = ""
    command: str = ""
    output: str = ""
    diff: str = ""
    commit_hash: str = ""

def parse_log_file(log_content: str) -> List[ReplayStep]:
    """
    Parses the content of an agent log file into a list of ReplayStep objects.
    """
    steps = []
    # Regular expression to split the log by "--- THOUGHT ---" sections
    thought_sections = re.split(r"--- THOUGHT ---", log_content)

    for section in thought_sections:
        if not section.strip():
            continue

        step = ReplayStep()

        # The thought is the first part of the section
        thought_match = re.match(r"(.*?)(?:--- COMMAND ---|--- GIT DIFF ---)", section, re.DOTALL)
        if thought_match:
            step.thought = thought_match.group(1).strip()
        elif "--- COMMAND ---" not in section and "--- GIT DIFF ---" not in section:
            step.thought = section.strip()

        # Extract command and output
        command_match = re.search(r"--- COMMAND ---\n(.*?)\n--- OUTPUT ---\n(.*?)(?=\n---|$)", section, re.DOTALL)
        if command_match:
            step.command = command_match.group(1).strip()
            step.output = command_match.group(2).strip()

        # Extract git diff
        diff_match = re.search(r"--- GIT DIFF ---\n(.*?)(?=\n---|$)", section, re.DOTALL)
        if diff_match:
            step.diff = diff_match.group(1).strip()
            # Try to find the commit hash in the diff output
            commit_match = re.search(r"Git commit: ([0-9a-f]+)", section, re.DOTALL)
            if commit_match:
                step.commit_hash = commit_match.group(1).strip()

        steps.append(step)

    return steps
