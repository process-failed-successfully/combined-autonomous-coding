import os
import sys
from pathlib import Path
from typing import Tuple
from shared.config import Config
from shared.logger import setup_logger
from shared.config_loader import load_config_from_file, ensure_config_exists
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from shared.utils import generate_agent_id

async def run_plan_logic(
    project_dir: Path,
    spec_file: Path,
    agent_type: str = "gemini",
    model: str = None,
    verbose: bool = False,
    profile: str = None,
    capture_output: bool = False
) -> Tuple[bool, str]:
    """
    Generates a feature plan from a spec file without executing it.
    Returns: (success, output_message)
    """

    # Setup logger
    # If capture_output is True, we disable console output to prevent TUI corruption
    logger, _ = setup_logger(name="plan_logic", log_file=None, verbose=verbose, console_output=not capture_output)

    if not capture_output:
        logger.info("--- Generating Agent Plan ---")

    # Basic validation
    if not spec_file or not spec_file.exists():
        msg = f"❌ Error: Spec file not found at: {spec_file}"
        if not capture_output:
            logger.error(msg)
        return False, msg

    # Load config from file to respect profiles and base settings
    ensure_config_exists()
    file_config = load_config_from_file(profile=profile)

    def resolve(cli_arg, config_key, default_val):
        if cli_arg is not None:
            return cli_arg
        if config_key in file_config:
            return file_config[config_key]
        return default_val

    # Create a minimal config for planning
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=resolve(model, "model", None),
        spec_file=spec_file,
        verbose=verbose,
        # Force settings for planning mode
        max_iterations=1,
        stream_output=False,
    )

    project_name = os.environ.get("PROJECT_NAME", config.project_dir.resolve().name)

    try:
        spec_content = config.spec_file.read_text()
        agent_id = generate_agent_id(project_name, spec_content, agent_type)
        config.agent_id = agent_id
    except Exception as e:
        if not capture_output:
            logger.warning(f"Could not generate agent ID: {e}")
        config.agent_id = generate_agent_id(project_name, "", agent_type)

    if not capture_output:
        logger.info(f"Generating plan for spec: {config.spec_file}")
        logger.info(f"Using agent: {config.agent_type}, Model: {config.model or 'default'}")

    # Dispatch to the correct agent type
    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }
    agent_class = agent_class_map.get(config.agent_type)

    if not agent_class:
        msg = f"Unknown agent type: {config.agent_type}"
        if not capture_output:
            logger.error(msg)
        return False, msg

    agent = agent_class(config)

    try:
        plan_generated = await agent.run_planning_session()

        if plan_generated:
            feature_file = config.project_dir / "feature_list.json"
            if feature_file.exists():
                content = feature_file.read_text()
                if not capture_output:
                    logger.info("\n--- Generated Plan (feature_list.json) ---")
                    print(content)
                    logger.info("------------------------------------")
                    logger.info("✅ Plan generated successfully.")
                return True, content
            else:
                msg = "Agent finished but did not produce a plan (feature_list.json)."
                if not capture_output:
                    logger.error(f"\n❌ {msg}")
                return False, msg
        else:
            msg = "Agent failed to generate a plan."
            if not capture_output:
                logger.error(f"\n❌ {msg}")
            return False, msg

    except Exception as e:
        msg = f"An error occurred during planning: {e}"
        if not capture_output:
            logger.error(msg, exc_info=True)
        return False, msg
