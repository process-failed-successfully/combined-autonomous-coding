import io
import contextlib
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from croniter import croniter
except ImportError:
    croniter = None

from shared.ask import run_ask_logic

class CronLabManager:
    """
    Manages Cron Lab operations: parsing, calculation, explanation, and generation.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def get_next_runs(self, expression: str, count: int = 5) -> Dict[str, Any]:
        """
        Calculates the next `count` run times for the given cron expression.
        """
        if not croniter:
            return {"error": "croniter library not found. Please install it.", "success": False}

        try:
            # Ensure expression is string
            expression = str(expression).strip()

            now = datetime.now()
            iter = croniter(expression, now)
            next_runs = []
            for _ in range(count):
                next_runs.append(iter.get_next(datetime))

            return {
                "expression": expression,
                "base_time": now,
                "next_runs": next_runs,
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    async def explain_expression(self, expression: str, agent_type: str = "gemini") -> str:
        """
        Uses AI to explain a cron expression.
        """
        prompt = f"Explain the following cron expression in plain English:\n\n```\n{expression}\n```\n\nBreak it down by fields (minute, hour, day, month, day of week)."

        return await self._run_ai(prompt, agent_type)

    async def generate_expression(self, description: str, agent_type: str = "gemini") -> str:
        """
        Uses AI to generate a cron expression from a description.
        """
        prompt = f"Generate a standard Cron expression for the following schedule description. Provide ONLY the expression in a code block, followed by a brief verification.\n\nDescription:\n{description}"

        return await self._run_ai(prompt, agent_type)

    async def _run_ai(self, prompt: str, agent_type: str) -> str:
        output_capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(output_capture):
                await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    verbose=False
                )
            return output_capture.getvalue()
        except Exception as e:
            return f"AI Error: {e}"

def run_cron_lab_cli(args):
    """CLI entry point for Cron Lab."""
    import asyncio
    project_dir = args.project_dir.resolve()
    manager = CronLabManager(project_dir)

    if args.action == "calc":
        if not args.expression:
            print("Error: Expression required.")
            sys.exit(1)

        result = manager.get_next_runs(args.expression, count=args.count)
        if result["success"]:
            print(f"Expression: {result['expression']}")
            print(f"Base Time: {result['base_time']}")
            print(f"Next {args.count} runs:")
            for dt in result["next_runs"]:
                print(f"  {dt}")
        else:
            print(f"Error: {result['error']}")
            sys.exit(1)

    elif args.action == "explain":
        if not args.expression:
            print("Error: Expression required.")
            sys.exit(1)

        print(f"Explaining: {args.expression}")
        response = asyncio.run(manager.explain_expression(args.expression, args.agent))
        print(response)

    elif args.action == "generate":
        if not args.description:
            print("Error: Description required.")
            sys.exit(1)

        print(f"Generating for: {args.description}")
        response = asyncio.run(manager.generate_expression(args.description, args.agent))
        print(response)

    sys.exit(0)
