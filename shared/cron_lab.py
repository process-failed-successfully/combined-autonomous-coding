import datetime
import io
import contextlib
from typing import List, Tuple, Optional
from croniter import croniter
from pathlib import Path
from shared.ask import run_ask_logic

class CronLabManager:
    """
    Manages Cron Lab operations: validation, calculation, and AI explanation/generation.
    """
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def validate(self, expression: str) -> Tuple[bool, str]:
        """
        Validates a cron expression.
        Returns: (is_valid, message)
        """
        if not expression:
            return False, "Expression cannot be empty."
        try:
            if croniter.is_valid(expression):
                return True, "Valid cron expression."
            else:
                return False, "Invalid cron expression."
        except Exception as e:
            return False, f"Error validating expression: {e}"

    def get_next_occurrences(self, expression: str, count: int = 5) -> List[datetime.datetime]:
        """
        Calculates the next N occurrences.
        """
        if not croniter.is_valid(expression):
            return []

        base_time = datetime.datetime.now()
        iter = croniter(expression, base_time)
        return [iter.get_next(datetime.datetime) for _ in range(count)]

    async def explain(self, expression: str, agent_type: str = "gemini") -> str:
        """
        Explains the cron expression using AI.
        """
        if not expression:
            return "Expression is empty."

        prompt = f"Explain the following cron expression in plain English. Be concise.\n\nExpression: {expression}"

        return await self._run_ai(prompt, agent_type)

    async def generate(self, description: str, agent_type: str = "gemini") -> str:
        """
        Generates a cron expression from description using AI.
        """
        if not description:
            return "Description is empty."

        prompt = f"Generate a standard cron expression for the following schedule. Output ONLY the cron expression, nothing else.\n\nSchedule: {description}"
        return await self._run_ai(prompt, agent_type)

    async def _run_ai(self, prompt: str, agent_type: str) -> str:
        """Helper to run AI query and capture output."""
        output_capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(output_capture):
                # We suppress stderr too if needed, but run_ask_logic uses logger which might go to stderr
                await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    verbose=False
                )

            response = output_capture.getvalue()

            # Clean up the output from run_ask_logic
            # It prints:
            # --- Answer ---
            # <content>
            # --------------

            if "--- Answer ---" in response:
                response = response.split("--- Answer ---")[1]

            if "--------------" in response:
                response = response.split("--------------")[0]

            return response.strip()

        except Exception as e:
            return f"AI Error: {e}"
