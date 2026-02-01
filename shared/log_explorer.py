import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class LogEntry:
    """Represents a single parsed log entry (timestamp, level, message)."""
    timestamp: str
    level: str
    message: str

@dataclass
class AgentStep:
    """Represents a semantic step in the agent's execution."""
    step_id: int
    timestamp: str
    description: str
    details: str
    type: str  # "INFO", "ERROR", "THOUGHT", "ACTION", "OUTPUT"

class LogParser:
    """Parses raw log files into structured AgentSteps."""

    # Matches: 10:00:01 - INFO - Message
    LOG_PATTERN = re.compile(r"^(\d{2}:\d{2}:\d{2}) - (INFO|DEBUG|WARNING|ERROR) - (.*)$")

    def parse_run(self, log_path: Path) -> List[AgentStep]:
        """Parses a log file and returns a list of steps."""
        entries = self._parse_entries(log_path)
        return self._group_steps(entries)

    def _parse_entries(self, log_path: Path) -> List[LogEntry]:
        entries = []
        if not log_path.exists():
            return []

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                current_entry = None
                message_lines = []

                for line in f:
                    match = self.LOG_PATTERN.match(line)
                    if match:
                        if current_entry:
                            current_entry.message = "\n".join(message_lines)
                            entries.append(current_entry)

                        current_entry = LogEntry(
                            timestamp=match.group(1),
                            level=match.group(2),
                            message=""  # Will be set later
                        )
                        message_lines = [match.group(3)]
                    else:
                        if current_entry:
                            # Append continuation lines, preserving indentation but removing EOL
                            message_lines.append(line.rstrip('\n'))

                if current_entry:
                    current_entry.message = "\n".join(message_lines)
                    entries.append(current_entry)

        except Exception as e:
            print(f"Error parsing log {log_path}: {e}")

        return entries

    def _group_steps(self, entries: List[LogEntry]) -> List[AgentStep]:
        """Groups raw entries into semantic steps."""
        steps = []
        step_id = 1

        for entry in entries:
            step_type = "INFO"

            # Simple heuristic categorization
            if entry.level == "ERROR":
                step_type = "ERROR"
            elif "Sending prompt" in entry.message or "Received response" in entry.message:
                step_type = "THOUGHT"
            elif "[Executing Bash]" in entry.message or "Running Bash" in entry.message:
                step_type = "ACTION"
            elif "[Output]" in entry.message:
                step_type = "OUTPUT"
            elif "Writing File" in entry.message or "Reading File" in entry.message:
                step_type = "ACTION"

            # Create step
            summary = entry.message.split('\n')[0]
            if len(summary) > 100:
                summary = summary[:97] + "..."

            steps.append(AgentStep(
                step_id=step_id,
                timestamp=entry.timestamp,
                description=summary,
                details=entry.message,
                type=step_type
            ))
            step_id += 1

        return steps
