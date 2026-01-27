import datetime
from pathlib import Path
from croniter import croniter
from shared.ask import run_ask_logic

class CronLabManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def validate(self, expression: str) -> bool:
        return croniter.is_valid(expression)

    def get_next_runs(self, expression: str, count: int = 10) -> list[str]:
        if not self.validate(expression):
            return []

        base = datetime.datetime.now()
        iter = croniter(expression, base)
        return [str(iter.get_next(datetime.datetime)) for _ in range(count)]

    async def explain_expression(self, expression: str, agent_type: str = "gemini") -> str:
        prompt = f"Explain the following cron expression in simple English:\n\n```\n{expression}\n```"
        success, output = await run_ask_logic(
            query=prompt,
            project_dir=self.project_dir,
            agent_type=agent_type,
            verbose=False,
            capture_output=True
        )
        return output if success else f"Error: {output}"

    async def generate_expression(self, description: str, agent_type: str = "gemini") -> str:
        prompt = f"Generate a standard cron expression for the following schedule. Provide ONLY the cron expression inside a code block.\n\nSchedule: {description}"
        success, output = await run_ask_logic(
            query=prompt,
            project_dir=self.project_dir,
            agent_type=agent_type,
            verbose=False,
            capture_output=True
        )
        return output if success else f"Error: {output}"
