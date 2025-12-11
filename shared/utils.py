"""
Shared Utilities
================

Common functions for autonomous coding agents.
"""

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from shared.config import Config

logger = logging.getLogger(__name__)


def log_startup_config(config: 'Config', logger: logging.Logger):
    """Logs the startup configuration in a clean format."""
    logger.info("\n" + "=" * 50)
    logger.info(f"  {config.agent_type.upper()} AUTONOMOUS CODING AGENT")
    logger.info("=" * 50)
    logger.info(f"  Project Dir  : {config.project_dir.resolve()}")
    logger.info(f"  Model        : {config.model}")
    iterations_str = config.max_iterations if config.max_iterations else 'Unlimited'
    logger.info(f"  Iterations   : {iterations_str}")

    if config.spec_file:
        logger.info(f"  Spec File    : {config.spec_file}")

    logger.info(
        f"  Verbose      : {'Enabled' if config.verbose else 'Disabled'}")

    if config.verify_creation:
        logger.info("  Verify Mode  : Enabled (Mocking responses)")

    logger.info("-" * 50 + "\n")


def get_file_tree(root_dir: Path) -> str:
    """Generate a concise file tree string."""
    tree_str = ""
    try:
        # Use git ls-files if available for cleaner output (respects
        # .gitignore)
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            tree_str = "Project Files:\n"
            for line in result.stdout.splitlines():
                tree_str += f"- {line}\n"
        else:
            # Fallback to simple walk
            tree_str = "Project Files (System):\n"
            for path in root_dir.rglob("*"):
                if path.is_file() and not any(p.name.startswith(".")
                                              for p in path.parents) and not path.name.startswith("."):
                    rel_path = path.relative_to(root_dir)
                    tree_str += f"- {rel_path}\n"
    except Exception as e:
        tree_str = f"Error generating file tree: {e}"

    return tree_str


def has_recent_activity(root_dir: Path, seconds: float = 60) -> bool:
    """Check if any file in the directory has been modified recently."""
    import time
    now = time.time()
    try:
        for path in root_dir.rglob("*"):
            # Ignore .git and other hidden dirs
            if ".git" in path.parts:
                continue
            if path.is_file():
                try:
                    mtime = path.stat().st_mtime
                    if now - mtime < seconds:
                        return True
                except OSError:
                    continue
    except Exception as e:
        logger.error(f"Error checking file activity: {e}")
    return False


async def execute_bash_block(
        command: str,
        cwd: Path,
        timeout: float = 120.0) -> str:
    """Execute a bash command block."""
    logger.info(f"[Executing Bash] {command}")
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,  # Prevent interactive hangs
            env=os.environ.copy(),
            preexec_fn=os.setsid  # Create a process group so we can kill the whole tree
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Bash command timed out after {timeout}s")
            try:
                # Kill the whole process group
                os.killpg(os.getpgid(process.pid), 15)  # SIGTERM
            except Exception:
                pass
            return f"Error: Command timed out after {timeout} seconds. If you intended to run a background process, please use '&' at the end of the command."

        output = ""
        if stdout:
            output += stdout.decode()
        if stderr:
            output += f"\nSTDERR:\n{stderr.decode()}"

        # Log truncated output to avoid spamming console
        display_output = output[:500] + ('...' if len(output) > 500 else '')
        logger.info(f"[Output]\n{display_output}")

        return output
    except Exception as e:
        logger.error(f"[Error] {e}")
        return str(e)


def execute_write_block(filename: str, content: str, cwd: Path) -> str:
    """Write content to a file."""
    logger.info(f"[Writing File] {filename}")
    try:
        file_path = cwd / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Successfully wrote {filename}"
    except Exception as e:
        logger.error(f"[Error] {e}")
        return str(e)


def execute_read_block(filename: str, cwd: Path) -> str:
    """Read content from a file with line numbers."""
    logger.info(f"[Reading File] {filename}")
    try:
        file_path = cwd / filename
        if not file_path.exists():
            return f"Error: File {filename} does not exist."

        content = file_path.read_text()
        lines = content.splitlines()
        numbered_lines = [f"{i + 1:4} | {line}" for i,
                          line in enumerate(lines)]
        return f"File: {filename}\n" + "\n".join(numbered_lines)
    except Exception as e:
        logger.error(f"[Error] {e}")
        return str(e)


async def execute_search_block(query: str, cwd: Path) -> str:
    """Search for a pattern in the codebase using grep."""
    logger.info(f"[Searching] {query}")
    try:
        # Recursive, line number, context=2
        cmd = f"grep -rnC 2 '{query}' ."
        process = await asyncio.create_subprocess_shell(
            cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        output = ""
        if stdout:
            output += stdout.decode()
        if not output:
            return f"No matches found for '{query}'"

        # Truncate if too long (approx 200 lines)
        lines = output.splitlines()
        if len(lines) > 200:
            return "\n".join(
                lines[:200]) + f"\n... ({len(lines) - 200} more lines truncated)"
        return output
    except Exception as e:
        logger.error(f"[Error] {e}")
        return str(e)


async def process_response_blocks(response_text: str,
                                  project_dir: Path,
                                  bash_timeout: float = 120.0,
                                  status_callback=None) -> Tuple[str,
                                                                 List[str]]:
    """
    Parse the response text for code blocks and execute them.
    Supported blocks:
    ```bash
    command
    ```
    ```write:filename
    content
    ```
    ```read:filename
    (empty or ignored)
    ```
    ```search:query
    (empty or ignored)
    ```

    Returns:
        tuple[str, List[str]]: execution_log, executed_actions
    """

    # Simple state machine parser
    lines = response_text.splitlines()
    execution_log = ""

    in_block = False
    block_type = None
    block_arg = None
    block_content: List[str] = []
    executed_actions = []

    for line in lines:
        if line.strip().startswith("```"):
            if in_block:
                # End of block
                content = "\n".join(block_content)
                if block_type == "bash":
                    if status_callback:
                        status_callback(f"Running Bash: {content[:50]}...")
                    output = await execute_bash_block(content, project_dir, timeout=bash_timeout)
                    execution_log += f"\n> {content}\n{output}\n"
                    executed_actions.append(f"Ran Bash: {content}")
                elif block_type == "write":
                    if status_callback:
                        status_callback(f"Writing File: {block_arg}")
                    output = execute_write_block(
                        block_arg, content, project_dir)
                    execution_log += f"\n> Write {block_arg}\n{output}\n"
                    executed_actions.append(f"Wrote File: {block_arg}")
                elif block_type == "read":
                    if status_callback:
                        status_callback(f"Reading File: {block_arg}")
                    output = execute_read_block(block_arg, project_dir)
                    execution_log += f"\n> Read {block_arg}\n{output}\n"
                    executed_actions.append(f"Read File: {block_arg}")
                elif block_type == "search":
                    if status_callback:
                        status_callback(f"Searching: {block_arg}")
                    output = await execute_search_block(block_arg, project_dir)
                    execution_log += f"\n> Search {block_arg}\n{output}\n"
                    executed_actions.append(f"Searched: {block_arg}")

                in_block = False
                block_type = None
                block_content = []
            else:
                # Start of block
                marker = line.strip()[3:]
                if marker == "bash":
                    in_block = True
                    block_type = "bash"
                elif marker.startswith("write:"):
                    in_block = True
                    block_type = "write"
                    block_arg = marker[6:].strip()
                elif marker.startswith("read:"):
                    in_block = True
                    block_type = "read"
                    block_arg = marker[5:].strip()
                elif marker.startswith("search:"):
                    in_block = True
                    block_type = "search"
                    block_arg = marker[7:].strip()
                # Ignore other blocks
        elif in_block:
            block_content.append(line)

    return execution_log, executed_actions
