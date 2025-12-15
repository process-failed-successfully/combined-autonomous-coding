import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path

from shared.config import Config
from shared.utils import has_recent_activity

logger = logging.getLogger(__name__)


class GeminiClient:
    """Handles interactions with the Gemini CLI."""

    def __init__(self, config: Config):
        self.config = config

    async def run_command(
        self, prompt: str, cwd: Path, status_callback=None
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
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        except FileNotFoundError:
            logger.error(
                "Gemini CLI not found. Please ensure 'gemini' is installed and in your PATH."
            )
            raise

        logger.debug("Sending prompt to stdin...")
        try:
            # We close stdin immediately after writing to ensure gemini knows
            # input is finished
            process.stdin.write(prompt.encode())
            await process.stdin.drain()
            process.stdin.close()
            logger.debug("Stdin closed. Waiting for output...")

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
                    status_callback(output_line=text)

            def on_stderr(text):
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

            # Wait loop with activity check
            timeout_counter = self.config.timeout
            last_stdout_len = 0
            last_stderr_len = 0

            while True:
                # Wait for tasks to complete or short timeout
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
                    # Activity detected, reset timeout
                    timeout_counter = self.config.timeout
                    last_stdout_len = current_stdout_len
                    last_stderr_len = current_stderr_len
                    continue

                # No output, decrement
                timeout_counter -= 5.0

                if timeout_counter > 0:
                    continue

                if has_recent_activity(self.config.project_dir, seconds=60):
                    logger.info(
                        "Agent timeout exceeded, but file activity detected. Extending wait by 60s..."
                    )
                    timeout_counter = 60.0  # Wait another minute
                    continue
                else:
                    logger.error(
                        f"Gemini CLI timed out ({self.config.timeout}s) and no recent file activity."
                    )
                    process.kill()
                    raise asyncio.TimeoutError

            # Ensure process is collected
            await process.wait()

            stdout = "".join(stdout_buf).encode()
            stderr = "".join(stderr_buf).encode()

            if process.returncode != 0:
                logger.error(f"Gemini process exited with code {process.returncode}")
                if stderr:
                    logger.error(f"STDERR: {stderr.decode()}")

        except Exception as e:
            logger.exception(f"Unexpected error running Gemini: {e}")
            raise

        stdout_text = stdout.decode().strip()
        stderr_text = stderr.decode().strip()

        if self.config.verbose and stderr_text:
            logger.debug(f"Gemini STDERR: {stderr_text}")

        # In TEXT mode, the whole stdout is the response content
        return {"content": stdout_text}
