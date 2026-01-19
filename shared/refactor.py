import difflib
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from shared.config import Config
from agents.shared.prompts import get_refactor_prompt
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)


class RefactorManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    async def refactor_file(
        self,
        target_file: Path,
        instruction: str,
        agent_type: str = "gemini",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Refactors a single file based on the instruction using an AI agent.

        Returns a dictionary containing:
        - original_content: str
        - new_content: str
        - diff: str
        - changed: bool
        """
        target_file = target_file.resolve()
        if not target_file.exists():
            raise FileNotFoundError(f"File not found: {target_file}")

        original_content = target_file.read_text(encoding="utf-8")

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
        prompt_template = get_refactor_prompt()

        prompt = prompt_template.format(
            instruction=instruction,
            filename=target_file.name,
            code=original_content
        )

        logger.info(f"Refactoring {target_file.name} with instruction: {instruction}")

        # Call Agent
        _, response, _ = await agent.run_agent_session(prompt)

        # Extract code block
        new_content = self._extract_code_block(response)

        # If extraction failed or returned empty, fallback to raw response if it looks like code?
        # Ideally the agent follows instructions. If not, we might get conversational noise.
        # But _extract_code_block tries to handle it.

        if not new_content.strip():
            # Fallback: if no code blocks, maybe the whole response is code?
            # But usually agents are chatty. Let's assume the agent failed if no code block.
            logger.warning("No code block found in agent response.")
            # Try to strip markdown if it's just the code
            if "def " in response or "class " in response or "import " in response:
                new_content = response.strip()
            else:
                new_content = original_content  # No change

        # Generate Diff
        diff_lines = list(difflib.unified_diff(
            original_content.splitlines(),
            new_content.splitlines(),
            fromfile=f"a/{target_file.relative_to(self.project_dir)}",
            tofile=f"b/{target_file.relative_to(self.project_dir)}",
            lineterm=""
        ))

        diff_text = "\n".join(diff_lines)
        changed = (new_content.strip() != original_content.strip())

        return {
            "original_content": original_content,
            "new_content": new_content,
            "diff": diff_text,
            "changed": changed
        }

    def apply_changes(self, target_file: Path, new_content: str):
        """Writes the new content to the file."""
        target_file.write_text(new_content, encoding="utf-8")

    def _extract_code_block(self, text: str) -> str:
        """Extracts content from markdown code blocks."""
        import re
        # Match ```language ... ```
        pattern = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)
        matches = pattern.findall(text)
        if matches:
            # Return the longest match (likely the file content)
            return max(matches, key=len).strip()

        # Fallback for no language specifier or different spacing
        return text.strip()
