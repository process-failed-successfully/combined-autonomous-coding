"""
Summarize Logic
===============

Logic for the 'summarize' command to explain git changes.
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
from agents.shared.prompts import get_summarize_prompt

logger = logging.getLogger(__name__)


def _get_git_diff_for_summary(project_dir: Path, target: Optional[str]) -> str:
    """
    Retrieves the git diff based on the target.

    Args:
        project_dir: The project root directory.
        target: The target for the summary (e.g., commit hash, range, or None for uncommitted).

    Returns:
        The content of the git diff.
    """
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        return ""

    try:
        if not target:
            # No target: summarize uncommitted changes (HEAD vs working dir)
            # We use HEAD to catch all changes (staged + unstaged)
            cmd = [git_path, "-C", str(project_dir), "diff", "HEAD"]
            description = "Uncommitted Changes"
        elif ".." in target:
            # Range: summarize the range
            cmd = [git_path, "-C", str(project_dir), "diff", target]
            description = f"Range {target}"
        else:
            # Single ref: summarize that commit (diff with parent)
            # We use show with -p (patch) but without the commit message to avoid redundancy if we just want the diff?
            # Actually, standardizing on 'diff' is safer. `git diff target~1..target`
            # But what if it's a root commit? Handled by git usually.
            # Let's try to interpret it as a commit hash and show changes introduced by it.
            cmd = [git_path, "-C", str(project_dir), "show", target]
            description = f"Commit {target}"

        result = subprocess.run(
            cmd,
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()
        if not output:
            return ""

        return f"--- {description} ---\n{output}"

    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting git diff for {target}: {e}")
        return ""


async def run_summarize_logic(
    project_dir: Path,
    target: Optional[str] = None,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False,
) -> bool:
    """
    Executes the 'summarize' logic.

    Args:
        project_dir: The project root directory.
        target: The target to summarize.
        agent_type: The type of agent to use.
        model: The model to use.
        verbose: Enable verbose logging.

    Returns:
        True if successful, False otherwise.
    """

    # Setup Config
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        verbose=verbose,
        max_iterations=1,  # Single shot
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

    # Prepare Content
    diff_content = _get_git_diff_for_summary(project_dir, target)

    if not diff_content:
        print(f"✅ No changes found to summarize for target: {target or 'Uncommitted'}")
        return True

    agent = agent_class(config)

    # Truncate if too huge? (Basic safeguard)
    MAX_CHARS = 100000
    if len(diff_content) > MAX_CHARS:
        print(f"⚠️  Diff is very large ({len(diff_content)} chars). Truncating to first {MAX_CHARS} chars.")
        diff_content = diff_content[:MAX_CHARS] + "\n... (truncated) ..."

    # Construct Prompt
    base_prompt = get_summarize_prompt()
    full_prompt = base_prompt.replace("{user_input}", diff_content)

    logger.info(f"Requesting Summary from {agent_type} agent...")
    print(f"--- Summarizing Changes with {agent_type} ---")

    try:
        status, response, actions = await agent.run_agent_session(full_prompt)

        # Output is streamed by the agent, but we print final separator
        print("\n--- Summary Complete ---")
        return True
    except Exception as e:
        logger.error(f"Error during summary session: {e}")
        return False
