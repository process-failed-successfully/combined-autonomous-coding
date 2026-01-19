"""
Commit Message Generator
========================

Logic for generating AI-powered commit messages based on git diffs.
"""

import logging
from pathlib import Path
from typing import Optional

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from agents.shared.prompts import get_commit_prompt

logger = logging.getLogger(__name__)

async def generate_commit_message(
    project_dir: Path,
    diff: str,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False,
) -> Optional[str]:
    """
    Generates a commit message based on the provided diff.

    Args:
        project_dir: The project root directory.
        diff: The git diff content.
        agent_type: The type of agent to use.
        model: The model to use.
        verbose: Enable verbose logging.

    Returns:
        The generated commit message string, or None if failed.
    """
    if not diff.strip():
        logger.warning("Empty diff provided to commit message generator.")
        return None

    # Setup Config
    # We disable stream_output to keep the UI clean while generating,
    # unless verbose is on, but even then, we want the result string.
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        verbose=verbose,
        max_iterations=1,  # Single shot
        stream_output=False, # We want the final text
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
        return None

    try:
        agent = agent_class(config)
    except Exception as e:
        logger.error(f"Failed to initialize agent {agent_type}: {e}")
        return None

    # Construct Prompt
    base_prompt = get_commit_prompt()
    full_prompt = base_prompt.replace("{diff}", diff)

    logger.info(f"Generating commit message with {agent_type} agent...")

    try:
        status, response, actions = await agent.run_agent_session(full_prompt)

        if not response:
            logger.error("Agent returned empty response.")
            return None

        return response.strip()
    except Exception as e:
        logger.error(f"Error during commit message generation: {e}")
        return None
