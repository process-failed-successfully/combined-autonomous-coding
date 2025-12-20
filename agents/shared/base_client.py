import asyncio
import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple, TYPE_CHECKING

from shared.config import Config
from shared.utils import has_recent_activity

if TYPE_CHECKING:
    from shared.agent_client import AgentClient

logger = logging.getLogger(__name__)


class BaseClient(ABC):
    """
    Abstract base class for all agent clients.
    Provides a common interface for interacting with different LLM-powered CLIs.
    """

    agent_client: Optional["AgentClient"] = None

    def __init__(self, config: Config) -> None:
        """
        Initialize the client with the provided configuration.

        Args:
            config (Config): The configuration object for the agent.
        """
        self.config = config

    @abstractmethod
    async def run_command(
        self,
        prompt: str,
        cwd: Path,
        status_callback: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run a command via the agent's CLI and return the parsed output.

        Args:
            prompt (str): The prompt to send to the agent.
            cwd (Path): The current working directory for the command execution.
            status_callback (Optional[Callable[..., Any]]): Optional callback for status updates.

        Returns:
            Dict[str, Any]: A dictionary containing the agent's response.
        """
        pass

    async def _run_subprocess(
        self,
        cmd: List[str],
        cwd: Path,
        env: Dict[str, str],
        input_str: Optional[str] = None,
        status_callback: Optional[Callable[..., Any]] = None,
        timeout: float = 120.0,
    ) -> Tuple[str, str, int]:
        """
        Helper to run a subprocess with streaming output and timeout handling.

        Args:
            cmd (List[str]): The command to execute.
            cwd (Path): Working directory.
            env (Dict[str, str]): Environment variables.
            input_str (Optional[str]): Input to send to stdin.
            status_callback (Optional[Callable]): Callback for status updates.
            timeout (float): Timeout in seconds.

        Returns:
            Tuple[str, str, int]: stdout, stderr content, and returncode.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdin=asyncio.subprocess.PIPE if input_str else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
        except FileNotFoundError:
            logger.error(f"Command not found: {cmd[0]}")
            raise

        if input_str:
            logger.debug("Sending input to stdin...")
            if process.stdin:
                process.stdin.write(input_str.encode())
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
        timeout_counter = timeout
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
                timeout_counter = timeout
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
                    f"Command timed out ({timeout}s) and no recent file activity."
                )
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                raise asyncio.TimeoutError

        # Ensure process is collected
        await process.wait()

        stdout = "".join(stdout_buf)
        stderr = "".join(stderr_buf)

        if process.returncode != 0:
            logger.error(f"Process exited with code {process.returncode}")
            if stderr:
                logger.debug(f"STDERR: {stderr}")

        return stdout, stderr, int(process.returncode or 0)
