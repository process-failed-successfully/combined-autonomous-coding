import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from shared.config import Config
from agents.shared.prompts import get_conflict_resolution_prompt
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

@dataclass
class Conflict:
    start_line: int  # 0-indexed line number of <<<<<<<
    sep_line: int    # 0-indexed line number of =======
    end_line: int    # 0-indexed line number of >>>>>>>
    base_line: Optional[int] # 0-indexed line number of ||||||| (diff3)
    ours_content: str
    theirs_content: str
    base_content: Optional[str] = None
    marker_ours: str = ""
    marker_theirs: str = ""

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

    def parse_conflicts(self, content: str) -> List[Conflict]:
        """
        Parses the content for git conflict markers.
        Handles standard and diff3 styles.
        """
        lines = content.splitlines(keepends=True)
        conflicts = []

        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("<<<<<<<"):
                start_line = i
                marker_ours = line.strip()

                # Scan for separator or base
                j = i + 1
                base_line = None
                sep_line = None
                end_line = None

                while j < len(lines):
                    if lines[j].startswith("|||||||"):
                        base_line = j
                    elif lines[j].startswith("======="):
                        sep_line = j
                    elif lines[j].startswith(">>>>>>>"):
                        end_line = j
                        marker_theirs = lines[j].strip()
                        break
                    j += 1

                if sep_line is not None and end_line is not None:
                    # Extract contents
                    # Ours: start+1 to (base if base else sep)
                    ours_end = base_line if base_line is not None else sep_line
                    ours_content = "".join(lines[start_line+1 : ours_end])

                    base_content = None
                    if base_line is not None:
                        base_content = "".join(lines[base_line+1 : sep_line])

                    theirs_content = "".join(lines[sep_line+1 : end_line])

                    conflicts.append(Conflict(
                        start_line=start_line,
                        sep_line=sep_line,
                        end_line=end_line,
                        base_line=base_line,
                        ours_content=ours_content,
                        theirs_content=theirs_content,
                        base_content=base_content,
                        marker_ours=marker_ours,
                        marker_theirs=marker_theirs
                    ))
                    i = end_line # Advance to end of conflict
            i += 1

        return conflicts

    def resolve_manual(self, file_path: Path, conflict_index: int, strategy: str) -> bool:
        """
        Resolves a specific conflict in a file.
        strategy: 'ours', 'theirs', or 'base'
        """
        content = file_path.read_text(encoding="utf-8")
        conflicts = self.parse_conflicts(content)

        if not conflicts or conflict_index >= len(conflicts):
            return False

        c = conflicts[conflict_index]
        resolution = ""

        if strategy == "ours":
            resolution = c.ours_content
        elif strategy == "theirs":
            resolution = c.theirs_content
        elif strategy == "base" and c.base_content is not None:
            resolution = c.base_content
        else:
            return False

        # Reconstruct content
        lines = content.splitlines(keepends=True)
        # Pre-conflict
        new_lines = lines[:c.start_line]
        # Resolved content
        new_lines.append(resolution)
        # Post-conflict
        new_lines.extend(lines[c.end_line+1:])

        file_path.write_text("".join(new_lines), encoding="utf-8")
        return True

    def resolve_all_manual(self, file_path: Path, strategy: str) -> int:
        """
        Resolves all conflicts in a file with the given strategy.
        Returns number of resolved conflicts.
        """
        resolved_count = 0
        while True:
            # Re-read and re-parse every time to handle shifting offsets safely
            content = file_path.read_text(encoding="utf-8")
            conflicts = self.parse_conflicts(content)
            if not conflicts:
                break

            # Resolve the first one
            if self.resolve_manual(file_path, 0, strategy):
                resolved_count += 1
            else:
                break # Should not happen if conflicts exist

        return resolved_count

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
