import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from shared.ask import run_ask_logic

class RegexLabManager:
    """Manages Regex Lab operations: matching, explaining, and generating."""

    def match_regex(self, pattern: str, text: str, flags: int = 0) -> Dict[str, Any]:
        """
        Matches a regex pattern against text.

        Args:
            pattern: The regex pattern.
            text: The text to search.
            flags: Regex flags (e.g. re.IGNORECASE).

        Returns:
            Dict containing match results.
        """
        try:
            matches = list(re.finditer(pattern, text, flags))
            results: List[Dict[str, Any]] = []

            for i, match in enumerate(matches):
                match_info = {
                    "index": i + 1,
                    "span": match.span(),
                    "full_match": match.group(0),
                    "groups": match.groups(),
                    "group_dict": match.groupdict()
                }
                results.append(match_info)

            return {
                "success": True,
                "count": len(matches),
                "matches": results
            }
        except re.error as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def explain_regex(self, pattern: str, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None) -> bool:
        """
        Explains a regex pattern using AI.
        """
        prompt = f"Explain the following regex pattern in detail:\n\n```regex\n{pattern}\n```"
        return await run_ask_logic(
            query=prompt,
            project_dir=project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False
        )

    async def generate_regex(self, description: str, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None) -> bool:
        """
        Generates a regex pattern from a description using AI.
        """
        prompt = f"Generate a Python regex pattern for the following description. Provide only the regex pattern first, wrapped in code blocks, followed by a brief explanation.\n\nDescription:\n{description}"
        return await run_ask_logic(
            query=prompt,
            project_dir=project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False
        )
