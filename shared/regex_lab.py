import re
import io
import contextlib
from pathlib import Path
from typing import Dict, Any
from shared.ask import run_ask_logic

class RegexLabManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def match_regex(self, pattern: str, text: str, flags: int = 0) -> Dict[str, Any]:
        """Matches pattern against text and returns results."""
        if not pattern:
            return {"error": "Pattern required."}

        try:
            matches = list(re.finditer(pattern, text, flags))
            if not matches:
                return {"matches": [], "count": 0}

            results = []
            for match in matches:
                m_data = {
                    "span": match.span(),
                    "group_0": match.group(0),
                    "groups": match.groups()
                }
                results.append(m_data)

            return {
                "matches": results,
                "count": len(matches)
            }

        except re.error as e:
            return {"error": str(e)}

    async def explain_regex(self, pattern: str, agent_type: str = "gemini") -> str:
        """Explains a regex pattern using AI."""
        if not pattern:
            return "Error: Pattern required."

        prompt = f"Explain the following regex pattern in detail:\n\n```regex\n{pattern}\n```"
        return await self._run_ai(prompt, agent_type)

    async def generate_regex(self, description: str, agent_type: str = "gemini") -> str:
        """Generates a regex pattern from description using AI."""
        if not description:
            return "Error: Description required."

        prompt = f"Generate a Python regex pattern for the following description. Provide only the regex pattern first, wrapped in code blocks, followed by a brief explanation.\n\nDescription:\n{description}"
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
