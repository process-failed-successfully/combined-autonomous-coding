import re
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class LogParser:
    """Parses agent log files into structured steps."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.steps = []

    def parse(self) -> List[Dict[str, str]]:
        """
        Parses the log file and returns a list of steps.
        Each step is a dictionary containing:
        - timestamp: The timestamp of the log entry.
        - level: The log level (INFO, DEBUG, etc.).
        - message: The raw message.
        """
        if not self.log_path.exists():
            # logger.error(f"Log file not found: {self.log_path}")
            return []

        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            # logger.error(f"Error reading log file: {e}")
            return []

        # Regex for log line: HH:MM:SS - LEVEL - Message
        # We need to handle multi-line messages, so we look for the start of a log line
        log_pattern = re.compile(r'^(\d{2}:\d{2}:\d{2}) - ([A-Z]+) - (.*)$', re.MULTILINE)

        matches = list(log_pattern.finditer(content))

        parsed_entries = []
        for i, match in enumerate(matches):
            timestamp = match.group(1)
            level = match.group(2)
            message_start = match.start(3)

            # Message continues until the start of the next match or end of file
            if i + 1 < len(matches):
                message_end = matches[i+1].start()
            else:
                message_end = len(content)

            message = content[message_start:message_end].strip()

            parsed_entries.append({
                "timestamp": timestamp,
                "level": level,
                "message": message
            })

        return parsed_entries

    def extract_agent_turns(self, steps: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Groups log entries into agent turns.
        """
        turns = []
        current_turn = {"logs": []}

        for step in steps:
            msg = step["message"]

            # Check for session header which usually marks start of a turn
            if "SESSION" in msg and "====" in msg:
                if current_turn["logs"]:
                    turns.append(current_turn)
                current_turn = {"logs": [], "header": msg}

            current_turn["logs"].append(step)

            # Try to extract key components if present in this log entry
            # This is naive but works for standard agent outputs
            lower_msg = msg.lower()
            if "thought:" in lower_msg:
                current_turn["thought"] = msg
            if "plan:" in lower_msg:
                current_turn["plan"] = msg
            if "command:" in lower_msg:
                current_turn["command"] = msg

        if current_turn["logs"]:
            turns.append(current_turn)

        return turns
