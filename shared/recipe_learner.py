import json
import logging
import re
import sys
import io
import contextlib
from pathlib import Path
from typing import List, Optional

from shared.recipes import RecipeManager
from shared.ask import run_ask_logic
from shared.cli_utils import get_latest_log_file

logger = logging.getLogger(__name__)

class LogParser:
    """Parses agent logs to extract executed commands."""

    def parse(self, log_path: Path) -> List[str]:
        commands = []
        if not log_path.exists():
            return []

        try:
            content = log_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            for line in lines:
                if "[Executing Bash]" in line:
                    parts = line.split("[Executing Bash]", 1)
                    if len(parts) > 1:
                        commands.append(parts[1].strip())

        except Exception as e:
            logger.error(f"Error parsing log: {e}")

        return commands

class RecipeLearner:
    """Learns recipes from previous agent runs."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.recipe_manager = RecipeManager(project_dir)

    async def learn_from_run(self, run_id: Optional[str], recipe_name: str, agent_type: str = "gemini", model: str = None) -> bool:
        """
        Analyzes a run and creates a recipe.
        """
        # 1. Find Log
        log_file = None
        if run_id and run_id != "last":
            # Assume run_id is the filename (or prefix)
            repo_root = Path(__file__).parent.parent
            logs_dir = repo_root / "agents/logs"
            log_file = logs_dir / f"{run_id}.log"
        else:
            log_file = get_latest_log_file()

        if not log_file or not log_file.exists():
            print(f"❌ Error: Log file not found for run '{run_id or 'latest'}'.")
            return False

        # 2. Parse Commands
        parser = LogParser()
        commands = parser.parse(log_file)

        if not commands:
            print("❌ Error: No executed commands found in the log.")
            return False

        print(f"Found {len(commands)} executed commands.")

        # 3. Ask AI to Generalize
        prompt = (
            f"I have executed the following sequence of bash commands to accomplish a task:\n"
            f"{json.dumps(commands, indent=2)}\n\n"
            f"Please create a generalized 'Recipe' (macro) named '{recipe_name}' that performs this task efficiently.\n"
            f"- Remove redundant steps (like ls, pwd, checking status multiple times).\n"
            f"- Generalize specific filenames to parameters if it makes sense, but prefer a concrete recipe if the task is specific.\n"
            f"- The recipe should be a list of shell commands.\n"
            f"- Return ONLY the recipe steps as a JSON list of strings. No markdown formatting, no explanations."
        )

        print(f"Asking {agent_type} to generate recipe '{recipe_name}'...")

        output_capture = io.StringIO()
        # We redirect stdout to capture the agent's output because run_ask_logic prints to stdout
        with contextlib.redirect_stdout(output_capture):
            success = await run_ask_logic(
                query=prompt,
                project_dir=self.project_dir,
                agent_type=agent_type,
                model=model,
                verbose=False
            )

        response = output_capture.getvalue()

        # If run_ask_logic failed, response might contain error info or be empty
        if not success and not response:
             print("❌ Error: Agent execution failed.")
             return False

        # 4. Parse Response
        recipe_steps = []
        try:
            # clean up response
            clean_resp = response.strip()
            # Remove markdown code blocks if present
            if "```" in clean_resp:
                match = re.search(r"```(?:json)?(.*?)```", clean_resp, re.DOTALL)
                if match:
                    clean_resp = match.group(1).strip()

            # Find the list start/end
            start = clean_resp.find('[')
            end = clean_resp.rfind(']')
            if start != -1 and end != -1:
                json_str = clean_resp[start:end+1]
                recipe_steps = json.loads(json_str)
            else:
                # If valid JSON list not found, maybe the agent outputted just text.
                # But we asked for JSON.
                # Let's try to parse non-empty lines as commands if JSON fails
                pass

        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse JSON from response: {e}")

        if not recipe_steps:
             print(f"❌ Error: Could not parse recipe steps from agent response.")
             print(f"Response was:\n{response}")
             return False

        # 5. Save Recipe
        if self.recipe_manager.add_recipe(recipe_name, recipe_steps):
            print(f"✅ Recipe '{recipe_name}' saved successfully!")
            print("Steps:")
            for step in recipe_steps:
                print(f"  - {step}")
            return True
        else:
            print("❌ Error: Failed to save recipe.")
            return False
