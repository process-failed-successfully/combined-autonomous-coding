"""
Cleaner Agent
=============

Runs after project sign-off to clean up temporary files.
"""

import logging
from pathlib import Path

from shared.config import Config
from agents.gemini.client import GeminiClient
from agents.gemini.agent import run_agent_session
from shared.utils import get_file_tree

logger = logging.getLogger(__name__)

def get_cleaner_prompt() -> str:
    prompt_path = Path(__file__).parent.parent.parent / "shared/prompts/cleaner_prompt.md"
    return prompt_path.read_text()

async def run_cleaner_agent(config: Config, agent_client=None):
    """
    Runs the cleaner agent to tidy up the project.
    """
    logger.info("Starting Cleaner Agent...")
    
    if agent_client:
        agent_client.report_state(current_task="Cleaning Project...")

    # We reuse the Gemini Client as the underlying engine
    client = GeminiClient(config)
    
    prompt = get_cleaner_prompt()
    
    # Run a limited number of iterations to ensure cleanup
    # Usually it should take 1-2 turns.
    max_cleaner_iterations = 5
    recent_history = []
    
    logger.info("Cleaner Agent Initialized. Scanning files...")

    for i in range(max_cleaner_iterations):
        logger.info(f"Cleaner Iteration {i+1}/{max_cleaner_iterations}")
        
        status, response, new_actions = await run_agent_session(
            client,
            prompt,
            recent_history,
            status_callback=None # We can add callback if needed
        )
        
        if new_actions:
            recent_history.extend(new_actions)
        
        # Check if cleanup report exists, which signals completion
        if (config.project_dir / "cleanup_report.txt").exists():
            logger.info("Cleanup successful. Report generated.")
            break
            
        if status == "error":
            logger.error("Cleaner Agent encountered an error.")
            break

    if agent_client:
        agent_client.report_state(current_task="Cleanup Complete")
