"""
Debug Logic
===========

Logic for the 'debug' command to run a command and analyze failures with AI.
"""

import subprocess
import logging
import sys
from pathlib import Path
from typing import Optional

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
    verbose: bool = False,
) -> bool:
    """
    Executes the 'debug' logic.

    Args:
        command: The shell command to run.
        project_dir: The project root directory.
        agent_type: The type of agent to use.
        model: The model to use.
        verbose: Enable verbose logging.

    Returns:
        True if the command succeeded, False if it failed (even if analysis ran).
    """

    print(f"--- Debugging Command: '{command}' ---")

    # 1. Run the command
    try:
        # we use shell=True to allow complex commands
        result = subprocess.run(
            command,
            shell=True,  # nosec
            cwd=project_dir,
            capture_output=True,
            text=True
        )
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        return False

    if result.returncode == 0:
        print("✅ Command executed successfully.")
        print(result.stdout)
        return True

    print(f"❌ Command failed with exit code {result.returncode}.")
    print("\n--- Output ---")
    print(result.stdout)
    print(result.stderr)
    print("----------------")
    print("\n🔍 Analyzing error with AI agent...")

    # 2. Setup Agent
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        verbose=verbose,
        max_iterations=1,
        stream_output=True,
    )

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

    # 3. Construct Prompt
    base_prompt = get_debug_prompt()
    error_output = (result.stdout + "\n" + result.stderr).strip()
    if not error_output:
        error_output = "(No output captured)"

    formatted_prompt = base_prompt.replace("{command}", command).replace("{error_output}", error_output)

    # Add context (file tree)
    file_tree = get_file_tree(project_dir)
    full_prompt = f"{formatted_prompt}\n\n### PROJECT CONTEXT\n\nFile Tree:\n{file_tree}\n"

    # 4. Run Agent
    try:
        # We reuse run_agent_session
        status, response, actions = await agent.run_agent_session(full_prompt)

        print("\n--- AI Analysis & Fix Suggestion ---")
        print(response)
        print("------------------------------------")
        return False # Return False because the original command failed
    except Exception as e:
        logger.error(f"Error during debug analysis: {e}")
        return False
