"""
Estimate Logic
==============

Logic for the 'estimate' command to estimate feature complexity and effort.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List

from shared.config import Config

logger = logging.getLogger(__name__)


def get_estimate_prompt() -> str:
    """Reads the estimate prompt template."""
    try:
        # shared/prompts/estimate_prompt.md
        prompt_path = Path(__file__).parent / "prompts" / "estimate_prompt.md"
        return prompt_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Error reading estimate prompt: {e}")
        return ""


def _collect_context(project_dir: Path, files: Optional[List[str]]) -> str:
    """
    Collects content from specified files to provide context.
    If no files specified, returns a generic message or scans key files (optional).
    """
    if not files:
        return "No specific files provided. Please analyze based on general knowledge and the feature description."

    context_parts = []
    for file_pattern in files:
        # Handle globbing
        try:
            matched_files = list(project_dir.glob(file_pattern))
            if not matched_files:
                # Try exact path
                p = project_dir / file_pattern
                if p.exists() and p.is_file():
                    matched_files = [p]

            for file_path in matched_files:
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                        # Truncate if too long?
                        if len(content) > 10000:
                            content = content[:10000] + "\n... (truncated)"
                        context_parts.append(f"--- File: {file_path.relative_to(project_dir)} ---\n{content}\n")
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Error processing pattern {file_pattern}: {e}")

    return "\n".join(context_parts)


async def run_estimate_logic(
    feature_description: str,
    project_dir: Path,
    files: Optional[List[str]] = None,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False,
) -> bool:
    """
    Executes the 'estimate' logic.

    Args:
        feature_description: The description of the feature to estimate.
        project_dir: The project root directory.
        files: List of file patterns to include as context.
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

    from agents.gemini import GeminiAgent
    from agents.cursor import CursorAgent
    from agents.local import LocalAgent
    from agents.openrouter import OpenRouterAgent

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

    try:
        agent = agent_class(config)
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        return False

    # Prepare Context
    context = _collect_context(project_dir, files)

    # Load Prompt
    prompt_template = get_estimate_prompt()
    if not prompt_template:
        print("❌ Error: Could not load estimate prompt template.", file=sys.stderr)
        return False

    # Construct Full Prompt
    full_prompt = prompt_template.format(
        user_input=feature_description,
        context=context
    )

    logger.info(f"Requesting Estimate from {agent_type} agent...")
    print(f"--- Estimating: {feature_description} ---")
    if files:
        print(f"Context files: {', '.join(files)}")

    try:
        status, response, actions = await agent.run_agent_session(full_prompt)

        # The agent streams output, so we just print a footer.
        if status == "error":
            print("\n❌ Estimation failed.")
            return False

        print("\n--- Estimation Complete ---")
        return True
    except Exception as e:
        logger.error(f"Error during estimation session: {e}")
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return False
