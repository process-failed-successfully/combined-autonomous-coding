import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

from shared.config import Config
from agents.shared.prompts import get_conflict_resolution_prompt
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

class ConflictResolver:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def find_conflicted_files(self) -> List[Path]:
        """Scans the project directory for files containing merge conflict markers."""
        conflicted_files = []
        for file_path in self.project_dir.rglob("*"):
            if file_path.is_file() and not any(part.startswith(".") for part in file_path.parts):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if "<<<<<<<" in content and "=======" in content and ">>>>>>>" in content:
                        conflicted_files.append(file_path)
                except Exception:
                    continue
        return conflicted_files

    async def resolve_file(
        self,
        target_file: Path,
        agent_type: str = "gemini",
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolves conflicts in a single file using an AI agent.

        Returns a dictionary containing:
        - original_content: str
        - resolved_content: str
        - resolved: bool
        """
        target_file = target_file.resolve()
        if not target_file.exists():
            raise FileNotFoundError(f"File not found: {target_file}")

        original_content = target_file.read_text(encoding="utf-8")

        # Basic check for markers
        if "<<<<<<<" not in original_content:
             return {
                "original_content": original_content,
                "resolved_content": original_content,
                "resolved": False,
                "message": "No conflict markers found."
            }

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
        prompt_template = get_conflict_resolution_prompt()

        prompt = prompt_template.format(
            filename=target_file.name,
            content=original_content
        )

        logger.info(f"Resolving conflicts in {target_file.name}")

        # Call Agent
        _, response, _ = await agent.run_agent_session(prompt)

        # Extract code block
        resolved_content = self._extract_code_block(response)

        # Sanity check: ensure markers are gone
        if "<<<<<<<" in resolved_content or ">>>>>>>" in resolved_content:
             logger.warning(f"Agent failed to remove all conflict markers in {target_file.name}")
             return {
                "original_content": original_content,
                "resolved_content": resolved_content,
                "resolved": False,
                "message": "Agent output still contains conflict markers."
            }

        return {
            "original_content": original_content,
            "resolved_content": resolved_content,
            "resolved": True
        }

    def resolve_manual(self, target_file: Path, strategy: str) -> Dict[str, Any]:
        """
        Resolves conflicts by accepting 'ours' or 'theirs' changes.

        Args:
            target_file: The file to resolve.
            strategy: 'ours' (HEAD) or 'theirs' (incoming).

        Returns:
            Dict result with resolved status and content.
        """
        if strategy not in ["ours", "theirs"]:
            raise ValueError("Strategy must be 'ours' or 'theirs'.")

        target_file = target_file.resolve()
        if not target_file.exists():
            raise FileNotFoundError(f"File not found: {target_file}")

        content = target_file.read_text(encoding="utf-8")

        lines = content.splitlines(keepends=True)
        resolved_lines = []

        in_conflict = False
        in_ours = False
        in_theirs = False
        # in_base is implied if in_conflict but not ours/theirs (between ||| and ===)

        current_ours = []
        current_theirs = []

        conflict_count = 0

        for line in lines:
            if line.startswith("<<<<<<<"):
                in_conflict = True
                in_ours = True
                in_theirs = False
                current_ours = []
                current_theirs = []
                conflict_count += 1
                continue

            if in_conflict:
                if line.startswith("|||||||"):
                    in_ours = False
                    # We are in base, ignore lines until =======
                    continue

                if line.startswith("======="):
                    in_ours = False
                    in_theirs = True
                    continue

                if line.startswith(">>>>>>>"):
                    # End of conflict block
                    if strategy == "ours":
                        resolved_lines.extend(current_ours)
                    elif strategy == "theirs":
                        resolved_lines.extend(current_theirs)

                    in_conflict = False
                    in_ours = False
                    in_theirs = False
                    continue

                if in_ours:
                    current_ours.append(line)
                elif in_theirs:
                    current_theirs.append(line)
                # else: in base, ignore
            else:
                resolved_lines.append(line)

        resolved_content = "".join(resolved_lines)

        return {
            "original_content": content,
            "resolved_content": resolved_content,
            "resolved": True,
            "conflicts_processed": conflict_count
        }

    def apply_resolution(self, target_file: Path, resolved_content: str):
        """Writes the resolved content to the file."""
        target_file.write_text(resolved_content, encoding="utf-8")

    def _extract_code_block(self, text: str) -> str:
        """Extracts content from markdown code blocks."""
        import re
        # Match ```language ... ```
        pattern = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)
        matches = pattern.findall(text)
        if matches:
            # Return the longest match (likely the file content)
            return max(matches, key=len).strip()

        # If no code blocks, check if the text itself looks like code (basic heuristic)
        # or just return the text stripped.
        return text.strip()
