import io
import contextlib
import croniter
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
from shared.ask import run_ask_logic

class CronLabManager:
    """Manages cron expression validation, calculation, and generation."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def validate(self, expression: str) -> Tuple[bool, str]:
        """Validates a cron expression."""
        if not expression:
            return False, "Empty expression."
        try:
            if not croniter.croniter.is_valid(expression):
                return False, "Invalid cron expression format."
            return True, "Valid expression."
        except Exception as e:
            return False, str(e)

    def get_next_runs(self, expression: str, count: int = 5) -> List[datetime]:
        """Calculates the next N run times."""
        try:
            base = datetime.now()
            iter = croniter.croniter(expression, base)
            return [iter.get_next(datetime) for _ in range(count)]
        except Exception:
            return []

    async def generate_expression(self, description: str, agent_type: str = "gemini") -> str:
        """Generates a cron expression from natural language using AI."""
        prompt = (
            f"Generate a standard cron expression for the following schedule description: '{description}'. "
            "Return ONLY the cron expression (e.g. '*/5 * * * *'), nothing else. "
            "Do not include markdown formatting or explanations."
        )

        capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(capture):
                await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    verbose=False
                )
        except Exception as e:
            return f"Error: {e}"

        return self._parse_output(capture.getvalue())

    async def explain_expression(self, expression: str, agent_type: str = "gemini") -> str:
        """Explains a cron expression in plain English using AI."""
        prompt = (
            f"Explain this cron expression in plain English: '{expression}'. "
            "Be concise."
        )

        capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(capture):
                await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    verbose=False
                )
        except Exception as e:
            return f"Error: {e}"

        return self._parse_output(capture.getvalue())

    def _parse_output(self, output: str) -> str:
        """Parses the output from run_ask_logic to extract the answer."""
        lines = output.splitlines()
        response_lines = []
        in_answer = False
        for line in lines:
            if "--- Answer ---" in line:
                in_answer = True
                continue
            if "--------------" in line and in_answer:
                break
            if in_answer:
                response_lines.append(line)

        result = "\n".join(response_lines).strip()
        # Clean up code blocks if any
        result = result.replace("```", "").strip()
        return result
