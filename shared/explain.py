"""
Explain Logic
=============

Logic for the 'explain' command to explain source code.
"""

import logging
from pathlib import Path
from typing import Optional, List

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from agents.shared.prompts import get_explain_prompt

logger = logging.getLogger(__name__)

async def run_explain_logic(
    args,
) -> bool:
    """
    Executes the 'explain' logic.

    Args:
        args: The argparse arguments.

    Returns:
        True if successful, False otherwise.
    """
    project_dir = args.project_dir
    files = args.file
    detail_level = args.detail
    diagram = args.diagram
    agent_type = args.agent
    model = args.model
    verbose = args.verbose

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

    # Read Files
    file_contents = ""
    for file_path_str in files:
        file_path = project_dir / file_path_str
        if file_path.exists() and file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                file_contents += f"\n--- File: {file_path_str} ---\n{content}\n"
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {e}")
        else:
            print(f"❌ File not found: {file_path}")
            return False

    if not file_contents:
        print("❌ No valid files to explain.")
        return False

    agent = agent_class(config)

    # Prepare Prompt Variables
    detail_instruction = "Provide a detailed walkthrough of the logic." if detail_level == "high" else "Keep the explanation brief and high-level."

    diagram_requested = "Yes" if diagram else "No"
    diagram_instruction = "Generate a Mermaid diagram (e.g., flowchat or sequence diagram) visualizing the logic." if diagram else "Do not generate a diagram."

    # Load and Format Prompt
    base_prompt = get_explain_prompt()
    full_prompt = base_prompt.replace("{detail_level}", detail_level)
    full_prompt = full_prompt.replace("{diagram_requested}", diagram_requested)
    full_prompt = full_prompt.replace("{file_content}", file_contents)
    full_prompt = full_prompt.replace("{detail_instruction}", detail_instruction)
    full_prompt = full_prompt.replace("{diagram_instruction}", diagram_instruction)

    logger.info(f"Requesting Explanation from {agent_type} agent...")
    print(f"--- Explaining {len(files)} file(s) with {agent_type} ---")

    try:
        status, response, actions = await agent.run_agent_session(full_prompt)
        print("\n--- Explanation Complete ---")
        return True
    except Exception as e:
        logger.error(f"Error during explain session: {e}")
        return False
