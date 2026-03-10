from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from croniter import croniter
from shared.ask import run_ask_logic

class CronLabManager:
    """Manages Cron Lab operations: next occurrences, explaining, and generating."""

    def parse(self, expression: str) -> Dict[str, Any]:
        """
        Parses a cron expression into its components.
        """
        if not croniter.is_valid(expression):
            return {
                "success": False,
                "error": "Invalid cron expression."
            }

        parts = expression.split()
        if len(parts) == 5:
            return {
                "success": True,
                "minute": parts[0],
                "hour": parts[1],
                "day_of_month": parts[2],
                "month": parts[3],
                "day_of_week": parts[4]
            }
        elif len(parts) == 6:
            return {
                "success": True,
                "second": parts[0],
                "minute": parts[1],
                "hour": parts[2],
                "day_of_month": parts[3],
                "month": parts[4],
                "day_of_week": parts[5]
            }
        else:
            # Fallback for complex expressions that is_valid accepted but don't split nicely
            return {
                "success": False,
                "error": f"Parsed {len(parts)} parts, expected 5 or 6."
            }

    def get_next_occurrences(self, expression: str, count: int = 5) -> Dict[str, Any]:
        """
        Validates a cron expression and calculates next occurrences.
        """
        try:
            if not croniter.is_valid(expression):
                return {
                    "success": False,
                    "error": "Invalid cron expression."
                }

            base = datetime.now()
            iter = croniter(expression, base)
            occurrences = []
            for _ in range(count):
                occurrences.append(iter.get_next(datetime).isoformat())

            return {
                "success": True,
                "occurrences": occurrences
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def explain_expression(self, expression: str, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None) -> bool:
        """
        Explains a cron expression using AI.
        """
        prompt = f"Explain the following cron expression in plain English:\n\n```\n{expression}\n```"
        return await run_ask_logic(
            query=prompt,
            project_dir=project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False
        )

    async def generate_expression(self, description: str, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None) -> bool:
        """
        Generates a cron expression from a description using AI.
        """
        prompt = f"Generate a standard cron expression for the following schedule description. Provide only the cron expression first, wrapped in code blocks, followed by a brief explanation.\n\nDescription:\n{description}"
        return await run_ask_logic(
            query=prompt,
            project_dir=project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False
        )
