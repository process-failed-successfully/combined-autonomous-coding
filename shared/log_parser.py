# shared/log_parser.py

import re
from typing import List, Dict, Any, NamedTuple
from dataclasses import dataclass

@dataclass
class CodeBlock:
    type: str
    content: str

@dataclass
class LogStep:
    thought: str
    actions: List[CodeBlock]

def parse_log_file(log_content: str) -> List[LogStep]:
    """
    Parses an agent log file into a structured list of steps.

    Each step represents a single turn of the agent's execution and contains:
    - thought: The agent's thought process and reasoning.
    - actions: A list of code blocks (e.g., bash, write) to be executed.
    """
    # Split the log file into individual turns based on the "Sending prompt" message
    turns = re.split(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - INFO - Sending prompt to Gemini...', log_content)

    parsed_steps = []
    for turn in turns:
        if not turn.strip():
            continue

        response_match = re.search(r'DEBUG - Response:\n(.*?)(?=\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - INFO)', turn, re.DOTALL)
        response_text = response_match.group(1).strip() if response_match else ""

        if not response_text:
            continue

        # Extract code blocks
        code_blocks_matches = re.finditer(r'```(.*?)\n(.*?)\n```', response_text, re.DOTALL)

        actions = []
        for match in code_blocks_matches:
            actions.append(CodeBlock(type=match.group(1).strip(), content=match.group(2).strip()))

        # The "thought" is the text without the code blocks
        thought = re.sub(r'```.*?\n.*?\n```', '', response_text, flags=re.DOTALL).strip()

        parsed_steps.append(LogStep(thought=thought, actions=actions))

    return parsed_steps
