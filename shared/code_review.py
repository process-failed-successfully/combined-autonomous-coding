"""
Code Review Logic
=================

Logic for the 'code-review' command to review code or diffs.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from agents.shared.prompts import get_code_review_prompt

logger = logging.getLogger(__name__)


def _get_git_diff(project_dir: Path) -> str:
    """Retrieves the git diff for the project (HEAD vs working directory)."""
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        return ""

    try:
        # Get diff of everything changed since HEAD (staged + unstaged)
        # We use HEAD to catch all uncommitted work.
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "diff", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting git diff: {e}")
        return ""


async def run_code_review_logic(
    project_dir: Path,
    files: Optional[List[str]] = None,
    diff: bool = False,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False,
) -> bool:
    """
    Executes the 'code-review' logic.

    Args:
        project_dir: The project root directory.
        files: Optional list of files to review.
        diff: If True, review the git diff (default if no files provided).
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

    agent = agent_class(config)

    # Prepare Content
    content_to_review = ""

    # 1. Specific Files
    if files:
        for file_path_str in files:
            file_path = project_dir / file_path_str
            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    content_to_review += f"\n--- File: {file_path_str} ---\n{content}\n"
                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {e}")
            else:
                logger.warning(f"File not found or not a file: {file_path}")

    # 2. Git Diff (if requested or if no files provided)
    if diff or not files:
        diff_content = _get_git_diff(project_dir)
        if diff_content:
            content_to_review += f"\n--- Git Diff (HEAD) ---\n{diff_content}\n"
        elif not files:
            print("✅ No changes found to review (git diff is empty).")
            return True

    if not content_to_review.strip():
        print("❌ No content found to review. Please specify files or ensure you have uncommitted changes.")
        return False

    # Construct Prompt
    base_prompt = get_code_review_prompt()
    full_prompt = base_prompt.replace("{user_input}", content_to_review)

    logger.info(f"Requesting Code Review from {agent_type} agent...")
    print(f"--- Starting Code Review with {agent_type} ---")

    try:
        status, response, actions = await agent.run_agent_session(full_prompt)

        # Output is streamed by the agent, but we print final separator
        print("\n--- Review Complete ---")
        return True
    except Exception as e:
        logger.error(f"Error during code review session: {e}")
        return False
