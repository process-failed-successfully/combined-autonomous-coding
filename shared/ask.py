import logging
import sys
from pathlib import Path
from typing import Optional

from shared.config import Config
from shared.config_loader import load_config_from_file, ensure_config_exists
from shared.logger import setup_logger
from shared.utils import generate_agent_id
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

async def run_ask_logic(args):
    """
    Logic for the 'ask' command.
    """
    # Setup logging
    # We use a temporary log file or just console output
    logger, _ = setup_logger(name="ask_logger", log_file=None, verbose=args.verbose, console_output=True)

    question = args.question
    project_dir = args.project_dir.resolve()

    logger.info(f"Asking agent: {question}")

    # Load configuration
    ensure_config_exists()
    file_config = load_config_from_file(profile=args.profile)

    def resolve(cli_arg, config_key, default_val):
        if cli_arg is not None:
            return cli_arg
        if config_key in file_config:
            return file_config[config_key]
        return default_val

    # Create Config
    config = Config(
        project_dir=project_dir,
        agent_type=args.agent,
        model=resolve(args.model, "model", None),
        verbose=args.verbose,
        stream_output=True, # Always stream for interactive ask
        max_iterations=1 # We only need one turn
    )

    # Generate a temporary agent ID
    agent_id = generate_agent_id(project_dir.name, question, args.agent)
    config.agent_id = agent_id

    # Select Agent Class
    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }
    agent_class = agent_class_map.get(config.agent_type)

    if not agent_class:
        logger.error(f"Unknown agent type: {config.agent_type}")
        sys.exit(1)

    # Initialize Agent
    agent = agent_class(config)

    # Construct the prompt
    # We want to force the agent to answer the question based on the codebase,
    # without trying to write code or modify files unless asked (even then, it's read-only effectively)
    # But wait, run_agent_session might try to execute blocks.
    # For 'ask', we mainly want the text response.

    prompt = f"""
QUESTION: {question}

INSTRUCTIONS:
You are an expert software engineer. Answer the user's question about the codebase located in {project_dir}.
Use the provided context (file tree) and your knowledge to answer.
If you need to read specific files to answer better, you can use the `read` tool (e.g. ```read:filename```).
Do NOT write any files or execute any bash commands that modify the system.
Your goal is to explain, analyze, or query the code.
"""

    # We need to hook into the agent's run_agent_session.
    # Most agents expose `run_agent_session(prompt, ...)`

    try:
        # We can reuse run_agent_session from the agent instance.
        # But we need to handle the output.
        # The agent's run_agent_session typically returns (status, response_text, actions).

        # NOTE: Some agents might not implement run_agent_session in the exact same way if they inherit differently,
        # but BaseAgent defines it.

        status, response, actions = await agent.run_agent_session(prompt)

        # If the agent used read tools, it might need another turn?
        # The current 'ask' implementation is single-turn for simplicity in this first iteration.
        # If we want multi-turn (Agent reads file -> LLM analyzes -> Final Answer), we might need a mini-loop.

        if any("Read File" in action for action in actions):
             # If it read files, we should probably give it a chance to synthesize the answer.
             # This is a simple 2-turn max loop for 'ask'
             logger.info("Agent read files. synthesizing answer...")
             follow_up_prompt = "Based on the files you read, please answer the original question."
             status, response, actions = await agent.run_agent_session(follow_up_prompt)

        # The response is usually printed by the agent logic (streaming) or we can print it here if not.
        # But BaseAgent usually handles streaming if config.stream_output is True.
        # If no stream, we print the final response.
        if not config.stream_output:
            print("\n--- Answer ---")
            print(response)

    except Exception as e:
        logger.error(f"Error during ask session: {e}", exc_info=True)
        sys.exit(1)
