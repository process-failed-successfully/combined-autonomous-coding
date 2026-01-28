from datetime import datetime
from typing import List, Tuple
from croniter import croniter
from shared.ask import run_ask_logic
from pathlib import Path
import io
import contextlib

class CronLabManager:
    """Manages parsing, validation, and explanation of cron expressions."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir or Path(".")

    def validate(self, expression: str) -> Tuple[bool, str]:
        """Validates a cron expression."""
        if not expression:
             return False, "Empty expression"
        if not croniter.is_valid(expression):
            return False, "Invalid cron expression format."
        return True, "Valid"

    def get_next_occurrences(self, expression: str, start_time: datetime = None, count: int = 5) -> List[datetime]:
        """Returns the next N occurrences of the cron schedule."""
        if not croniter.is_valid(expression):
            return []

        if start_time is None:
            start_time = datetime.now()

        iter = croniter(expression, start_time)
        occurrences = []
        for _ in range(count):
            occurrences.append(iter.get_next(datetime))

        return occurrences

    async def explain_expression(self, expression: str, agent_type: str = "gemini", model: str = None) -> str:
        """Uses AI to explain the cron expression in natural language."""
        if not croniter.is_valid(expression):
            return "Invalid expression cannot be explained."

        prompt = f"Explain this cron expression in plain English: '{expression}'. Be concise. Do not include introductory text."

        output_capture = io.StringIO()
        # We need to ensure we don't stream to real stdout if possible,
        # but run_ask_logic hardcodes stream_output=True.
        # Redirecting stdout captures it.

        try:
            with contextlib.redirect_stdout(output_capture):
                await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    model=model,
                    verbose=False
                )
        except Exception as e:
            return f"Error using AI agent: {e}"

        # Parse output - run_ask_logic prints "--- Answer ---" ...
        output = output_capture.getvalue()
        if "--- Answer ---" in output:
            parts = output.split("--- Answer ---")
            if len(parts) > 1:
                answer = parts[1].split("--------------")[0].strip()
                return answer

        return output.strip()
