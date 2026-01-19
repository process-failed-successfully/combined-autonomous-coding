import logging
from pathlib import Path
from typing import Optional
from shared.config import Config
from agents.shared.prompts import get_test_generation_prompt
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
import re

logger = logging.getLogger(__name__)

class TestGenerator:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    async def generate_tests(
        self,
        target_file: Path,
        output_file: Optional[Path] = None,
        framework: str = "pytest",
        agent_type: str = "gemini",
        model: Optional[str] = None
    ) -> bool:
        """
        Generates tests for the target file.
        """
        target_file = target_file.resolve()

        if not target_file.exists():
            print(f"Error: Target file '{target_file}' does not exist.")
            return False

        # Default output path: tests/test_<filename>.py
        if not output_file:
            tests_dir = self.project_dir / "tests"
            tests_dir.mkdir(exist_ok=True)

            test_filename = f"test_{target_file.stem}.py"
            output_file = tests_dir / test_filename

        # Ensure parent dir exists if output_file is specified
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            display_output = output_file.relative_to(self.project_dir)
        except ValueError:
            display_output = output_file

        print(f"Generating {framework} tests for: {target_file.name}")
        print(f"Output will be saved to: {display_output}")

        # Setup Agent
        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False,
            max_iterations=1,
            stream_output=False,
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent = agent_class(config)
        prompt_template = get_test_generation_prompt()

        try:
            code_content = target_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file: {e}")
            return False

        # Format prompt
        # Use relative path for context to avoid confusing the agent with absolute paths
        try:
            rel_path = str(target_file.relative_to(self.project_dir))
        except ValueError:
            rel_path = target_file.name

        prompt = prompt_template.format(
            framework=framework,
            file_path=rel_path,
            code=code_content
        )

        print("Requesting test generation from agent...")
        try:
            _, response, _ = await agent.run_agent_session(prompt)

            # Extract code block
            # Look for ```python ... ``` or just ``` ... ```
            code_block_match = re.search(r"```(?:python)?\n(.*?)```", response, re.DOTALL)

            if code_block_match:
                test_code = code_block_match.group(1).strip()
            else:
                # Fallback: assume the whole response is code if no blocks found?
                # But agents often chat. Let's warn.
                # If content starts with "import" or "from", it might be code.
                lines = response.strip().splitlines()
                if lines and (lines[0].startswith("import") or lines[0].startswith("from")):
                     test_code = response.strip()
                else:
                    print("Warning: No code block found in agent response. Saving full response.")
                    test_code = response.strip()

            output_file.write_text(test_code, encoding="utf-8")
            print(f"✅ Test file saved: {display_output}")
            return True

        except Exception as e:
            logger.error(f"Error generating tests: {e}")
            print(f"❌ Error: {e}")
            return False
