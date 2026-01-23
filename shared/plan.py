import sys
import os
from pathlib import Path
import logging

from shared.config import Config
from shared.logger import setup_logger
from shared.config_loader import load_config_from_file, ensure_config_exists
from shared.utils import generate_agent_id
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

async def run_plan_logic(
    project_dir: Path,
    spec_file: str,
    agent_type: str = "gemini",
    model: str = None,
    verbose: bool = False,
    profile: str = None,
    capture_output: bool = False
):
    """
    Generates a feature plan from a spec file.
    Returns (success, message).
    """
    # Setup logging if not capturing output (CLI mode), otherwise rely on existing logger or silence
    if not capture_output:
        logger, _ = setup_logger(name="plan_logger", log_file=None, verbose=verbose, console_output=True)
    else:
        # If capturing output, we might want to log to a string or just use the root logger
        # For TUI, we probably don't want console output messing up the UI.
        # We'll use a logger that doesn't print to console if possible, or just the root one.
        logger = logging.getLogger("plan_logger")
        # Ensure it doesn't propagate to root if root prints to console
        logger.propagate = False
        # Add a string handler if we want to capture logs, but TUI usually redirects stdout/stderr or uses a widget.
        # For now, let's assume TUI handles logging via a separate handler attached to root.
        # But we need to disable the console handler if it was added by setup_logger elsewhere?
        # Simpler: just use the logger.

    if not spec_file:
        return False, "Error: spec_file is required."

    spec_path = Path(spec_file)
    if not spec_path.is_absolute():
        spec_path = project_dir / spec_path

    if not spec_path.exists():
        return False, f"Error: Spec file not found: {spec_path}"

    # Load config
    ensure_config_exists()
    file_config = load_config_from_file(profile=profile)

    def resolve(cli_arg, config_key, default_val):
        if cli_arg is not None:
            return cli_arg
        if config_key in file_config:
            return file_config[config_key]
        return default_val

    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=resolve(model, "model", None),
        spec_file=str(spec_path), # Config expects Path or str? Config definition in main.py used args.spec which is str or Path?
        # main.py: spec_file=args.spec. args.spec is string from argparse unless typed.
        # main.py parser: --spec [path] default app_spec.txt.
        # Config expects spec_file to be Path object usually.
        # Let's check Config definition.
        verbose=verbose,
        max_iterations=1,
        stream_output=not capture_output, # Disable stream if capturing for TUI?
    )
    # Fix spec_file type if Config expects Path
    config.spec_file = spec_path

    project_name = os.environ.get("PROJECT_NAME", config.project_dir.resolve().name)

    try:
        spec_content = config.spec_file.read_text()
        agent_id = generate_agent_id(project_name, spec_content, agent_type)
        config.agent_id = agent_id
    except Exception as e:
        logger.warning(f"Could not generate agent ID: {e}")
        config.agent_id = generate_agent_id(project_name, "", agent_type)

    logger.info(f"Generating plan for spec: {config.spec_file}")
    logger.info(f"Using agent: {config.agent_type}, Model: {config.model or 'default'}")

    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }
    agent_class = agent_class_map.get(config.agent_type)

    if not agent_class:
        return False, f"Unknown agent type: {config.agent_type}"

    agent = agent_class(config)

    try:
        # Run planning
        plan_generated = await agent.run_planning_session()

        if plan_generated:
            feature_file = config.project_dir / "feature_list.json"
            if feature_file.exists():
                content = feature_file.read_text()
                msg = "Plan generated successfully."
                if not capture_output:
                    logger.info("\n--- Generated Plan (feature_list.json) ---")
                    print(content)
                    logger.info("------------------------------------")
                    logger.info(f"✅ {msg}")
                return True, content
            else:
                msg = "Agent finished but did not produce feature_list.json."
                logger.error(f"\n❌ {msg}")
                return False, msg
        else:
            msg = "Agent failed to generate a plan."
            logger.error(f"\n❌ {msg}")
            return False, msg

    except Exception as e:
        msg = f"An error occurred during planning: {e}"
        logger.error(msg, exc_info=True)
        return False, msg
