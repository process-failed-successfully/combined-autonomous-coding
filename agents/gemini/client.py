import json
import logging
import os
from typing import Any, Dict, Optional, Callable
from pathlib import Path

from shared.config import Config
from agents.shared.base_client import BaseClient

logger = logging.getLogger(__name__)


class GeminiClient(BaseClient):
    """Handles interactions with the Gemini CLI."""

    def __init__(self, config: Config):
        super().__init__(config)

    async def run_command(
        self,
        prompt: str,
        cwd: Path,
        status_callback: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run a gemini CLI command and return the parsed JSON output.
        """
        logger.debug("Starting gemini subprocess...")

        if self.config.verify_creation:
            logger.info("VERIFICATION MODE: Returning mock response.")
            mock_content = {
                "London": 45.0,
                "New York": 25.0,
                "Paris": 30.0,
                "Tokyo": 100.0,
            }
            mock_json = json.dumps(mock_content, indent=4)
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": f"I will create the output.json file.\n```write:output.json\n{mock_json}\n```"
                                }
                            ]
                        }
                    }
                ]
            }

        # We assume 'gemini' is in the PATH.
        # Ensure we ask for TEXT output for better streaming
        cmd = ["gemini", "--output-format", "text", "--approval-mode", "yolo"]

        if self.config.model and self.config.model != "auto":
            cmd.extend(["--model", self.config.model])

        env = os.environ.copy()

        # Run in subprocess, passing PROMPT via stdin to avoid shell arg limits
        try:
            stdout, stderr, _returncode = await self._run_subprocess(
                cmd,
                cwd,
                env,
                input_str=prompt,
                status_callback=status_callback,
                timeout=self.config.timeout,
            )
        except Exception as e:
            logger.exception(f"Unexpected error running Gemini: {e}")
            raise

        stdout_text = stdout.strip()
        stderr_text = stderr.strip()

        if self.config.verbose and stderr_text:
            logger.debug(f"Gemini STDERR: {stderr_text}")

        # In TEXT mode, the whole stdout is the response content
        return {"content": stdout_text}
