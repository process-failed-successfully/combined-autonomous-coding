"""
Ask Logic
=========

Logic for the 'ask' command to query the codebase.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from agents.shared.prompts import get_ask_prompt
from shared.utils import get_file_tree
from shared.work_session import WorkSessionManager

logger = logging.getLogger(__name__)

async def run_ask_logic(
    query: str,
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    files: Optional[List[str]] = None,
    verbose: bool = False,
) -> bool:
    """
    Executes the 'ask' logic.

    Args:
        query: The user's question.
        project_dir: The project root directory.
        agent_type: The type of agent to use.
        model: The model to use.
        files: Optional list of files to include in the context.
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

    agent = agent_class(config)  # type: ignore

    # Prepare Context
    context_files_content = ""
    active_session_info = ""

    # Check for active session if no files provided
    if not files:
        session_manager = WorkSessionManager(project_dir)
        active_session = session_manager.get_active_session()
        if active_session:
            files = active_session.files
            active_session_info = f"Active Session: {active_session.name}\n"
            if active_session.description:
                active_session_info += f"Description: {active_session.description}\n"
            if active_session.notes:
                active_session_info += "Session Notes:\n" + "\n".join(active_session.notes) + "\n"

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
    base_prompt = get_ask_prompt()
    formatted_prompt = base_prompt.replace("{user_question}", query)

    # Append Context
    full_prompt = f"{formatted_prompt}\n\n### PROJECT CONTEXT\n\nFile Tree:\n{file_tree}\n"

    if active_session_info:
        full_prompt += f"\n{active_session_info}\n"

    if context_files_content:
        full_prompt += f"\nSelected Files Content:\n{context_files_content}"
    else:
        # If no specific files provided, maybe include README or app_spec if they exist?
        # For now, let's keep it minimal to avoid huge context, unless the user asks for it.
        # But a naive "ask" might need some content.
        # Let's verify if we should add README.md automatically.
        readme_path = project_dir / "README.md"
        if readme_path.exists():
             try:
                content = readme_path.read_text(encoding="utf-8", errors="ignore")
                full_prompt += f"\n--- File: README.md ---\n{content}\n"
             except Exception:
                 pass

    logger.info(f"Asking {agent_type} agent: {query}")

    try:
        # We reuse run_agent_session but we expect it might try to execute actions
        # if the prompt wasn't strict enough. The prompt says "No Execution".
        status, response, actions = await agent.run_agent_session(full_prompt)

        # We output the response directly to stdout for the user
        print("\n--- Answer ---")
        print(response)
        print("--------------")

        return True
    except Exception as e:
        logger.error(f"Error during ask session: {e}")
        return False
