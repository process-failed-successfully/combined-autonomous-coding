"""
Debug Logic
===========

Logic for the 'debug' command to analyze command failures using AI.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from agents.shared.prompts import get_debug_prompt
from shared.utils import get_file_tree

logger = logging.getLogger(__name__)

async def run_debug_logic(
    command: str,
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    files: Optional[List[str]] = None,
    verbose: bool = False,
) -> bool:
    """
    Executes the 'debug' logic.

    Args:
        command: The shell command to run and debug.
        project_dir: The project root directory.
        agent_type: The type of agent to use.
        model: The model to use.
        files: Optional list of files to include in the context.
        verbose: Enable verbose logging.

    Returns:
        True if successful (command passed or analysis complete), False otherwise.
    """
    if not command:
        logger.error("No command provided to debug.")
        return False

    print(f"--- Running: {command} ---")

    # Run the command
    try:
        # We use shell=True to support complex commands like "python test.py && echo ok"
        # Security Note: This is intended for local dev use.
        result = subprocess.run(  # nosec
            command,
            cwd=project_dir,
            shell=True,
            capture_output=True,
            text=True
        )
    except Exception as e:
        logger.error(f"Failed to execute command: {e}")
        return False

    # If the command succeeded, we have nothing to debug (unless user forced it, but for now let's exit)
    if result.returncode == 0:
        print(result.stdout)
        print("\n✅ Command executed successfully. No debugging needed.")
        return True

    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    print(f"\n❌ Command failed with exit code {result.returncode}. Starting AI debug analysis...")

    # Setup Config
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        verbose=verbose,
        max_iterations=1, # Single shot
        stream_output=True,
    )

    # Initialize Agent
    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }

    agent_class = agent_class_map.get(agent_type)
    if not agent_class:
        logger.error(f"Unknown agent type: {agent_type}")
        return False

    agent = agent_class(config)

    # Prepare Context
    context_files_content = ""
    if files:
        for file_path_str in files:
            file_path = project_dir / file_path_str
            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    context_files_content += f"\n--- File: {file_path_str} ---\n{content}\n"
                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {e}")
            else:
                logger.warning(f"File not found or not a file: {file_path}")

    # Gather additional context if specific files aren't enough or aren't provided
    # We always include the file tree
    file_tree = get_file_tree(project_dir)

    # Construct Prompt
    base_prompt = get_debug_prompt()

    # Format the prompt
    prompt_variables = {
        "command": command,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_code": str(result.returncode),
        "file_tree": file_tree,
        "context_files": context_files_content
    }

    # We construct the final prompt manually to ensure structure
    full_prompt = f"{base_prompt}\n\n"
    full_prompt += f"### COMMAND\n{command}\n\n"
    full_prompt += f"### OUTPUT (Exit Code: {result.returncode})\n"
    full_prompt += f"STDOUT:\n{result.stdout}\n"
    full_prompt += f"STDERR:\n{result.stderr}\n\n"
    full_prompt += f"### PROJECT CONTEXT\n\nFile Tree:\n{file_tree}\n"

    if context_files_content:
        full_prompt += f"\nSelected Files Content:\n{context_files_content}"

    logger.info(f"Asking {agent_type} agent to debug command.")

    try:
        # We reuse run_agent_session
        status, response, actions = await agent.run_agent_session(full_prompt)

        # The response is streamed by the agent if configured, but we also print the final result if needed.
        # Since we set stream_output=True, the agent usually prints to stdout.
        # But run_agent_session returns the full response string too.

        # Check if agent already printed. If so, we might be duplicating?
        # Agents usually print chunks.
        # Let's just print a separator.

        print("\n--- AI Debug Analysis Complete ---")

        return True
    except Exception as e:
        logger.error(f"Error during debug session: {e}")
        return False
