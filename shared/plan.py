import os
import sys
from pathlib import Path
import logging
import io
import contextlib

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
    agent_type: str,
    model: str | None,
    spec_file: str | Path | None,
    verbose: bool = False,
    profile: str | None = None,
    capture_output: bool = False
) -> tuple[bool, str]:
    """
    Generates a feature plan from a spec file without executing it.

    Returns:
        tuple[bool, str]: (Success, Output Message)
    """

    # Setup output capture if needed
    output_buffer = io.StringIO()

    # We use a context manager to potentially redirect stdout/stderr if capturing output
    # However, logger might be configured to write to original stdout/stderr.
    # We'll attach a StreamHandler to the logger if capturing.

    log_stream = output_buffer if capture_output else None

    # Setup logger. If capturing output, we want the logs to go to our buffer.
    # Note: setup_logger sets up the root logger.
    # We disable console_output if capturing to avoid polluting stdout/stderr which might break TUI.
    logger, _ = setup_logger(name="plan_logger", log_file=None, verbose=verbose, console_output=not capture_output)

    # If capturing, we need to add a handler that writes to our buffer
    captured_handler = None
    if capture_output:
        captured_handler = logging.StreamHandler(output_buffer)
        formatter = logging.Formatter('%(message)s') # Simple format for TUI
        captured_handler.setFormatter(formatter)
        logger.addHandler(captured_handler)
        # Also redirect print
        redirector = contextlib.redirect_stdout(output_buffer)
        redirector.__enter__()

    try:
        logger.info("--- Generating Agent Plan ---")

        if not spec_file:
             msg = "❌ Error: A valid spec file is required."
             logger.error(msg)
             return False, output_buffer.getvalue() if capture_output else msg

        spec_path = Path(spec_file)
        if not spec_path.exists():
            msg = f"❌ Error: Spec file '{spec_path}' does not exist."
            logger.error(msg)
            return False, output_buffer.getvalue() if capture_output else msg

        # Load config
        ensure_config_exists()
        file_config = load_config_from_file(profile=profile)

        def resolve(arg_val, config_key, default_val):
            if arg_val is not None:
                return arg_val
            if config_key in file_config:
                return file_config[config_key]
            return default_val

        config = Config(
            project_dir=project_dir,
            agent_type=agent_type,
            model=resolve(model, "model", None),
            spec_file=spec_path,
            verbose=verbose,
            max_iterations=1,
            stream_output=False,
        )

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
            msg = f"Unknown agent type: {config.agent_type}"
            logger.error(msg)
            return False, output_buffer.getvalue() if capture_output else msg

        agent = agent_class(config)

        # Run planning session
        plan_generated = await agent.run_planning_session()

        if plan_generated:
            feature_file = config.project_dir / "feature_list.json"
            if feature_file.exists():
                logger.info("\n--- Generated Plan (feature_list.json) ---")
                plan_content = feature_file.read_text()
                print(plan_content) # This goes to stdout/buffer
                logger.info("------------------------------------")
                logger.info("✅ Plan generated successfully.")
                return True, output_buffer.getvalue() if capture_output else "Plan generated successfully."
            else:
                msg = "❌ Agent finished but did not produce a plan (feature_list.json)."
                logger.error(msg)
                return False, output_buffer.getvalue() if capture_output else msg
        else:
            msg = "❌ Agent failed to generate a plan."
            logger.error(msg)
            return False, output_buffer.getvalue() if capture_output else msg

    except Exception as e:
        msg = f"An error occurred during planning: {e}"
        logger.error(msg, exc_info=True)
        return False, output_buffer.getvalue() if capture_output else msg

    finally:
        if capture_output:
            if captured_handler:
                logger.removeHandler(captured_handler)
            redirector.__exit__(None, None, None)
