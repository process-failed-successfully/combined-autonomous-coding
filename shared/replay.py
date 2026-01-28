import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Iterator

@dataclass
class Action:
    command: str
    output: str = ""
    status: str = "UNKNOWN"

@dataclass
class Turn:
    turn_id: int
    timestamp: str
    thought: str = ""
    actions: List[Action] = field(default_factory=list)
    prompt_summary: str = ""

class ReplayManager:
    """Manages the replay of an agent run."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        # Assume logs are in agents/logs relative to repo root (which is parent of project_dir if running in dev mode,
        # but in production/docker, logs might be elsewhere.
        # based on main.py: repo_root = Path(__file__).parent.parent; logs_dir = repo_root / "agents/logs"
        # We will try to locate logs dir dynamically.
        self.logs_dir = self._find_logs_dir()

    def _find_logs_dir(self) -> Optional[Path]:
        # heuristic: check common locations
        candidates = [
            self.project_dir / "agents/logs",
            self.project_dir.parent / "agents/logs",
            Path("agents/logs").resolve(),
        ]
        for p in candidates:
            if p.exists() and p.is_dir():
                return p
        return None

    def load_run(self, run_id: Optional[str] = None) -> Optional[Path]:
        """Finds the log file for the given run_id or the latest run."""
        if not self.logs_dir:
            return None

        if run_id:
            log_file = self.logs_dir / f"{run_id}.log"
            if log_file.exists():
                return log_file
            return None

        # Get latest
        try:
            logs = sorted(self.logs_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            if logs:
                return logs[0]
        except OSError:
            pass
        return None

    def parse_log(self, log_path: Path) -> List[Turn]:
        """Parses the log file into a list of Turns."""
        turns = []
        current_turn = None
        current_action = None

        # Regex patterns
        timestamp_pat = re.compile(r"^(\d{2}:\d{2}:\d{2}) - (INFO|DEBUG|WARNING|ERROR) - (.*)$")

        try:
            content = log_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Error reading log: {e}")
            return []

        lines = content.splitlines()

        turn_counter = 1

        for line in lines:
            match = timestamp_pat.match(line)
            if not match:
                # Continuation line
                if current_action and current_action.output:
                     current_action.output += "\n" + line
                elif current_turn and current_turn.thought is not None:
                     current_turn.thought += "\n" + line
                continue

            timestamp, level, message = match.groups()

            # Start of a new turn (sending prompt)
            if "Sending Augmented Prompt" in message or "Sending prompt to" in message:
                if current_turn:
                    turns.append(current_turn)
                current_turn = Turn(turn_id=turn_counter, timestamp=timestamp)
                current_turn.prompt_summary = "Prompt sent..."
                turn_counter += 1
                current_action = None
                continue

            # Response received (Thought)
            if "Received response from" in message or "Response:" in message:
                current_action = None
                if current_turn:
                    # If line is "Response:", the next lines are the content
                    if message.strip() == "Response:":
                        current_turn.thought = "" # Will be filled by continuation lines
                    else:
                        # Sometimes it's logged as "Received response..." and debug logs follow
                        pass
                continue

            # Capture output of response logging if we are in a turn and haven't started actions
            if current_turn and not current_turn.actions and level == "DEBUG" and not message.startswith("Response:"):
                 # This is heuristic, capturing the response text which is usually logged in DEBUG
                 # But we must be careful not to capture other debug info.
                 # Actually, agent.py logs: logger.debug(f"Response:\n{response_text}")
                 # So the line "Response:" matches above, and subsequent lines are continuation.
                 pass

            # Actions
            # "[Executing Bash] command"
            if "[Executing Bash]" in message:
                cmd = message.split("[Executing Bash]")[1].strip()
                current_action = Action(command=cmd)
                if current_turn:
                    current_turn.actions.append(current_action)
                else:
                    # Orphan action? create a dummy turn
                    current_turn = Turn(turn_id=turn_counter, timestamp=timestamp, thought="(Orphaned Action)")
                    current_turn.actions.append(current_action)
                    turn_counter += 1
                continue

            # Action Output
            # "[Output]: output"
            if "[Output]" in message:
                out = message.split("[Output]")[1].strip()
                if current_action:
                    current_action.output = out
                continue

        # Append last turn
        if current_turn:
            turns.append(current_turn)

        return turns

    def replay(self, run_id: Optional[str] = None, speed: float = 0.5, auto: bool = False):
        """Interactively replays the session."""
        log_file = self.load_run(run_id)
        if not log_file:
            print(f"❌ Log file not found for run_id: {run_id or 'latest'}")
            return

        print(f"--- Replaying Run: {log_file.stem} ---")
        print(f"Log File: {log_file}")

        turns = self.parse_log(log_file)
        if not turns:
            print("No turns found in log. Is the format correct?")
            return

        print(f"Found {len(turns)} turns.\n")

        for turn in turns:
            self._render_turn(turn)

            if not auto:
                input("\n[Press Enter for next turn...]")
            else:
                time.sleep(speed)

            print("-" * 60)

    def _render_turn(self, turn: Turn):
        print(f"\n🟢 [Turn {turn.turn_id}] {turn.timestamp}")

        if turn.thought:
            print("\n🧠 [Thought]")
            # Truncate thought if too long for display?
            # Or formatted.
            print(turn.thought.strip())

        if turn.actions:
            print("\n⚡ [Actions]")
            for action in turn.actions:
                print(f"  $ {action.command}")
                if action.output:
                    # Indent output
                    out_lines = action.output.splitlines()
                    preview = "\n    ".join(out_lines[:10])
                    if len(out_lines) > 10:
                        preview += "\n    ... (truncated)"
                    print(f"    {preview}")
        else:
            print("\n(No actions taken)")
