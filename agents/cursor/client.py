import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from shared.utils import log_system_health
from agents.shared.base_client import BaseClient

logger = logging.getLogger(__name__)


class CursorClient(BaseClient):
    """Handles interactions with the Cursor Agent CLI."""

    def _get_mock_response(self) -> Dict[str, Any]:
        """Return a mock response for verification mode."""
        logger.info("VERIFICATION MODE: Returning mock response.")
        mock_content = {
            "London": 45.0,
            "New York": 25.0,
            "Paris": 30.0,
            "Tokyo": 100.0,
        }
        return {
            "choices": [
                {
                    "message": {
                        "content": f"I will create the output.json file.\n```write:output.json\n{json.dumps(mock_content, indent=4)}\n```"
                    }
                }
            ],
            "content": f"I will create the output.json file.\n```write:output.json\n{json.dumps(mock_content, indent=4)}\n```",
        }

    def _build_cursor_command(self, prompt: str, cwd: Path) -> List[str]:
        """Build the cursor-agent CLI command."""
        cmd = [
            "cursor-agent",
            "agent",
            prompt,
            "--print",
            "--output-format",
            "text",
            "--force",
            "--workspace",
            str(cwd.resolve()),
        ]

        if self.config.model:
            cmd.extend(["--model", self.config.model])

        return cmd

    def _get_cursor_env(self) -> Dict[str, str]:
        """Build the environment for the cursor-agent subprocess."""
        env = {}
        safe_keys = {
            "PATH",
            "HOME",
            "USER",
            "SHELL",
            "TERM",
            "TMPDIR",
            "LANG",
            "LC_ALL",
            "LC_CTYPE",
            "DISPLAY",
            "XAUTHORITY",
            "SSH_AUTH_SOCK",
            "SSH_AGENT_PID",
            "WORKSPACE_DIR",
            "PROJECT_NAME",
            "NODE_ENV",
            "NVM_DIR",
        }

        for k, v in os.environ.items():
            if (
                k in safe_keys
                or k.startswith("CURSOR_")
                or k.startswith("XDG_")
                or k.startswith("npm_")
            ):
                env[k] = v

        env["NO_OPEN_BROWSER"] = "1"
        return env

    async def run_command(
        self,
        prompt: str,
        cwd: Path,
        status_callback: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run a cursor-agent CLI command and return the parsed output.
        """
        logger.debug("Starting cursor-agent subprocess...")

        if self.config.verify_creation:
            return self._get_mock_response()

        cmd = self._build_cursor_command(prompt, cwd)
        env = self._get_cursor_env()

        def wrapped_status_callback(current_task=None, output_line=None):
            if status_callback:
                # If no specific task is provided, use a default one for Cursor
                task = current_task or "Cursor Generating..."
                status_callback(current_task=task, output_line=output_line)

        try:
            stdout, stderr, returncode = await self._run_subprocess(
                cmd,
                cwd,
                env,
                status_callback=wrapped_status_callback,
                timeout=self.config.timeout,
            )

            if returncode != 0:
                error_msg = f"Cursor process exited with code {returncode}"
                logger.error(error_msg)

                if stderr:
                    logger.error(f"STDERR: {stderr}")

                    if "resource_exhausted" in stderr:
                        raise Exception("Cursor Agent failed due to Resource Exhaustion (Quota/Rate Limit). Please try again later or switch models.")

                # Special handling for SIGTERM (143) to identify it clearly
                if returncode == 143 or returncode == -15:
                    health_info = log_system_health()
                    raise Exception(
                        f"Cursor Agent received SIGTERM (Exit 143). This may be due to OOM or external termination. {health_info} {error_msg}"
                    )

                # For other errors, we also raise so the agent loop can retry
                raise Exception(error_msg)

        except asyncio.TimeoutError:
            logger.error(
                f"Cursor Agent CLI timed out ({self.config.timeout}s) and no recent output or file activity."
            )
            raise
        except Exception as e:
            if not isinstance(e, (asyncio.TimeoutError, Exception)) or "Cursor process exited" not in str(e):
                logger.exception(f"Unexpected error running Cursor Agent: {e}")
            raise

        # In TEXT mode, raw stdout is content
        return {"content": stdout.strip()}
