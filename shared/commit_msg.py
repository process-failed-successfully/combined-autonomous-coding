import subprocess
import logging
import shutil
from pathlib import Path
from typing import Optional
from shared.config import Config
from agents.shared.prompts import get_commit_message_prompt
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

async def generate_commit_message(
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None
) -> Optional[str]:
    """
    Generates a commit message based on the current staged changes using the specified agent.
    """
    # 1. Get staged diff
    git_path = shutil.which("git")
    if not git_path:
        logger.error("Git not found.")
        return None

    try:
        # Get diff of staged changes
        diff_proc = subprocess.run(
            [git_path, "-C", str(project_dir), "diff", "--cached"],
            capture_output=True, text=True, check=True
        )
        diff_content = diff_proc.stdout.strip()

        if not diff_content:
            # Fallback: Check if there are unstaged changes we might want to warn about?
            # Or maybe the user hasn't staged anything yet.
            # But run_commit in main.py stages everything with `git add -A`.
            # So if diff is empty, it means no changes at all.
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting git diff: {e}")
        return None

    # 2. Setup Agent
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        verbose=False,
        max_iterations=1,
        stream_output=False,
    )

    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }

    agent_class = agent_class_map.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")

    agent = agent_class(config)

    # 3. Construct Prompt
    prompt_template = get_commit_message_prompt()
    # Truncate diff if too large to avoid token limits (naive truncation)
    MAX_DIFF_LEN = 10000
    if len(diff_content) > MAX_DIFF_LEN:
        diff_content = diff_content[:MAX_DIFF_LEN] + "\n... (diff truncated)"

    prompt = prompt_template.replace("{diff}", diff_content)

    # 4. Run Agent
    print("Generating commit message...")
    try:
        _, response, _ = await agent.run_agent_session(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating commit message: {e}")
        return None
