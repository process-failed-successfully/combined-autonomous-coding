import sys
from pathlib import Path
from typing import Optional
from shared.ask import run_ask_logic
import io
import contextlib

class TranspilerManager:
    """
    Manages code transpilation using AI.
    """
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    async def transpile(self, source_code: str, source_lang: str, target_lang: str, agent_type: str = "gemini", model: Optional[str] = None) -> str:
        """
        Transpiles code from one language to another using AI.
        """
        if not source_code.strip():
            return ""

        prompt = f"""
Act as an expert code transpiler.
Convert the following {source_lang} code to {target_lang}.
Provide ONLY the converted code block. Do not include explanations, markdown formatting (like ```python), or chatty conversational text.
Just the raw code.

Source Code ({source_lang}):
{source_code}
"""
        # Capture stdout because run_ask_logic prints to stdout
        output_capture = io.StringIO()
        success = False
        try:
            with contextlib.redirect_stdout(output_capture):
                success = await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    model=model,
                    verbose=False
                )
        except Exception as e:
            return f"Error: {e}"

        result = output_capture.getvalue().strip()

        # Cleanup markdown blocks if the agent ignored instructions
        if result.startswith("```"):
            lines = result.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            result = "\n".join(lines)

        if not success:
             # If run_ask_logic failed (returned False), the output might contain error info
             if not result:
                 return "Error: AI generation failed."

        return result.strip()
