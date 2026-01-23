"""
AI-Powered Git Utilities
========================

Logic for AI-assisted git operations like commit message generation.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from agents.shared.prompts import get_commit_message_prompt

logger = logging.getLogger(__name__)


def _get_staged_diff(project_dir: Path) -> str:
    """Retrieves the staged git diff."""
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        return ""

    try:
        cmd = [git_path, "-C", str(project_dir), "diff", "--cached"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting staged diff: {e}")
        return ""


async def generate_commit_message_logic(
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
) -> Optional[str]:
    """
    Generates a commit message using AI based on staged changes.

    Args:
        project_dir: The project root directory.
        agent_type: The type of agent to use.
        model: The model to use.

    Returns:
        The generated commit message string, or None if failed/empty diff.
    """

    # 1. Get Staged Diff
    diff_content = _get_staged_diff(project_dir)

    if not diff_content:
        # If no staged changes, we cannot generate a commit message for a commit that won't happen.
        return None

    # 2. Setup Config & Agent
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        max_iterations=1,
        stream_output=False,  # Capture output directly
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
        return None

    agent = agent_class(config)

    # 3. Construct Prompt
    base_prompt = get_commit_message_prompt()
    # Basic check to avoid extremely large prompts
    MAX_CHARS = 50000
    if len(diff_content) > MAX_CHARS:
        diff_content = diff_content[:MAX_CHARS] + "\n... (truncated)"

    full_prompt = base_prompt.replace("{user_input}", diff_content)

    # 4. Run Agent
    try:
        # We assume run_agent_session works for this.
        # Note: Some agents might require 'stream_output=True' to function correctly depending on implementation details,
        # but Config controls the printing. 'response' should be captured regardless.

        status, response, actions = await agent.run_agent_session(full_prompt)

        if response:
            return response.strip()
        return None

    except Exception as e:
        logger.error(f"Error during commit message generation: {e}")
        return None
