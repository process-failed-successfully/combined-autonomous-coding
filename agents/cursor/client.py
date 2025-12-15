import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Any, Dict, List

from shared.config import Config
from shared.utils import log_system_health

logger = logging.getLogger(__name__)


class CursorClient:
    """Handles interactions with the Cursor Agent CLI."""

    def __init__(self, config: Config):
        self.config = config

    async def run_command(
        self, prompt: str, cwd: Path, status_callback=None
    ) -> Dict[str, Any]:
        """
        Run a cursor-agent CLI command and return the parsed JSON output.
        """
        logger.debug("Starting cursor-agent subprocess...")

        if self.config.verify_creation:
            logger.info("VERIFICATION MODE: Returning mock response.")
            mock_content = {
                "London": 45.0,
                "New York": 25.0,
                "Paris": 30.0,
                "Tokyo": 100.0,
            }
            # Cursor agent typically returns a flat 'content' or 'response' in some wrappers,
            # or simply text in 'text'. Let's match the parsing logic: 'candidates' -> 'content' -> 'parts' -> 'text'
            # OR 'content' key.
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"I will create the output.json file.\n```write:output.json\n{json.dumps(mock_content, indent=4)}\n```"
                        }
                    }
                ],
                # Our parser handles "candidates" or "content".
                # Let's provide "content" directly for simplicity as per
                # agent.py logic line 178
                "content": f"I will create the output.json file.\n```write:output.json\n{json.dumps(mock_content, indent=4)}\n```",
            }

        # Build command
        # cursor-agent agent [prompt] --print --output-format text --force
        # --workspace [cwd]
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

        # Create a filtered environment to avoid hitting ARG_MAX on macOS
        # We start with a clean dict and copy only essential or safe variables
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
            # Node/NPM related
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

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        except FileNotFoundError:
            logger.error(
                "Cursor Agent CLI not found. Please ensure 'cursor-agent' is installed and in your PATH."
            )
            raise

        logger.debug("Waiting for output...")

        try:
            # Helper for streaming interaction
            async def _read_stream(stream, callback, buffer_list):
                while True:
                    line = await stream.readline()
                    if line:
                        decoded = line.decode()
                        if callback:
                            callback(decoded)
                        buffer_list.append(decoded)
                    else:
                        break

            stdout_buf: List[str] = []
            stderr_buf: List[str] = []

            # Helper callbacks
            def on_stdout(text):
                if self.config.stream_output:
                    sys.stdout.write(text)
                    sys.stdout.flush()
                if status_callback:
                    # Stream output to status callback
                    # We pass current_task to ensure the user knows it's active
                    status_callback(
                        current_task="Cursor Generating...", output_line=text
                    )

            def on_stderr(text):
                # Always log stderr to debug/info for visibility
                if text.strip():
                    logger.warning(f"Cursor Agent STDERR: {text.strip()}")

                if self.config.stream_output:
                    sys.stderr.write(text)
                    sys.stderr.flush()

            # Create tasks
            tasks = [
                asyncio.create_task(
                    _read_stream(process.stdout, on_stdout, stdout_buf)
                ),
                asyncio.create_task(
                    _read_stream(process.stderr, on_stderr, stderr_buf)
                ),
            ]

            timeout_counter = self.config.timeout
            last_stdout_len = 0
            last_stderr_len = 0

            while True:
                # Wait for a short interval to check activity
                # We use a shorter wait here to frequently check for output flow
                done, pending = await asyncio.wait(tasks, timeout=5.0)

                if not pending:
                    break

                # Check for Output Activity (Streaming)
                current_stdout_len = len(stdout_buf)
                current_stderr_len = len(stderr_buf)

                if (
                    current_stdout_len > last_stdout_len
                    or current_stderr_len > last_stderr_len
                ):
                    # We have activity! Reset timeout counter
                    # But we don't reset the *loop* timeout, we just don't decrement the counter
                    # Actually, we should probably implement a custom timeout counter since asyncio.wait argument is a max wait.
                    # Let's simplify: execution continues as long as we have output OR file activity.
                    timeout_counter = self.config.timeout
                    last_stdout_len = current_stdout_len
                    last_stderr_len = current_stderr_len
                    continue

                # No output activity this interval. Decrement counter.
                timeout_counter -= 5.0

                if timeout_counter > 0:
                    continue

                # Timeout exceeded? Check file activity as last resort.
                from shared.utils import has_recent_activity

                if has_recent_activity(self.config.project_dir, seconds=60):
                    logger.info(
                        "Agent timeout exceeded, but file activity detected. Extending wait by 60s..."
                    )
                    (
                        status_callback(
                            current_task="Waiting (File Activity Detected)..."
                        )
                        if status_callback
                        else None
                    )
                    timeout_counter = 60.0
                    continue
                else:
                    logger.error(
                        f"Cursor Agent CLI timed out ({self.config.timeout}s) and no recent output or file activity."
                    )
                    process.kill()
                    raise asyncio.TimeoutError

            await process.wait()
            stdout = "".join(stdout_buf).encode()
            stderr = "".join(stderr_buf).encode()

            if process.returncode != 0:
                error_msg = f"Cursor process exited with code {process.returncode}"
                logger.error(error_msg)

                if stderr:
                    logger.error(f"STDERR: {stderr.decode()}")

                # Special handling for SIGTERM (143) to identify it clearly
                if process.returncode == 143 or process.returncode == -15:
                    health_info = log_system_health()
                    raise Exception(
                        f"Cursor Agent received SIGTERM (Exit 143). This may be due to OOM or external termination. {health_info} {error_msg}"
                    )

                # For other errors, we also raise so the agent loop can retry
                raise Exception(error_msg)

        except Exception as e:
            logger.exception(f"Unexpected error running Cursor Agent: {e}")
            raise

        stdout_text = stdout.decode().strip()
        stderr_text = stderr.decode().strip()

        if self.config.verbose and stderr_text:
            logger.debug(f"Cursor STDERR: {stderr_text}")

        # In TEXT mode, raw stdout is content
        return {"content": stdout_text}
