import sys
import os
import logging
from pathlib import Path
from shared.config import Config
from shared.config_loader import load_config_from_file, ensure_config_exists
from shared.utils import generate_agent_id
from shared.logger import setup_logger

async def run_plan_logic(
    project_dir: Path,
    spec_file: Path,
    agent_type: str,
    model: str = None,
    verbose: bool = False,
    capture_output: bool = False,
    profile: str = None
) -> tuple[bool, str]:
    """
    Generates a feature plan from a spec file without executing it.

    Args:
        project_dir: The project directory.
        spec_file: Path to the app_spec.txt file.
        agent_type: The type of agent to use (gemini, cursor, etc.).
        model: Optional model override.
        verbose: Enable verbose logging.
        capture_output: If True, returns (success, output_string) instead of printing.
        profile: Optional configuration profile name.

    Returns:
        (success, message)
    """
    # Capture logs if requested, otherwise use standard setup
    log_stream = None
    logger_handler = None

    if capture_output:
        import io
        log_stream = io.StringIO()
        # We still want to use the shared logger setup but redirect console output
        # However, setup_logger configures the root logger.
        # For TUI, we might want to rely on the existing logger configuration or create a new one.
        # Simplest approach for TUI: capture logging by adding a handler or intercepting.
        # But `run_plan` in main.py uses a specific logger name "plan_logger".
        # Let's use a local logger.
        logger = logging.getLogger("plan_logic")
        logger.setLevel(logging.INFO if not verbose else logging.DEBUG)
        logger_handler = logging.StreamHandler(log_stream)
        logger_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(logger_handler)
        # Prevent propagation to avoid double logging in TUI
        logger.propagate = False
    else:
        logger, _ = setup_logger(name="plan_logger", log_file=None, verbose=verbose, console_output=True)

    def log_info(msg): logger.info(msg)
    def log_error(msg): logger.error(msg)

    try:
        log_info("--- Generating Agent Plan ---")

        if not spec_file or not spec_file.exists():
            msg = f"❌ Error: Spec file not found at {spec_file}"
            log_error(msg)
            return False, msg if capture_output else ""

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
            logger.warning(f"Could not generate agent ID: {e}")
            config.agent_id = generate_agent_id(project_name, "", agent_type)

        log_info(f"Generating plan for spec: {config.spec_file}")
        log_info(f"Using agent: {config.agent_type}, Model: {config.model or 'default'}")

        # Lazy import agents
        from agents.gemini import GeminiAgent
        from agents.cursor import CursorAgent
        from agents.local import LocalAgent
        from agents.openrouter import OpenRouterAgent

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }
        agent_class = agent_class_map.get(config.agent_type)

        if not agent_class:
            msg = f"Unknown agent type: {config.agent_type}"
            log_error(msg)
            return False, msg if capture_output else ""

        agent = agent_class(config)

        try:
            # We need to make sure run_planning_session is awaited if it's async,
            # or run appropriately. In main.py it is awaited: `await agent.run_planning_session()`
            plan_generated = await agent.run_planning_session()

            if plan_generated:
                feature_file = config.project_dir / "feature_list.json"
                if feature_file.exists():
                    content = feature_file.read_text()
                    log_info("\n--- Generated Plan (feature_list.json) ---")
                    # If capturing, we append the content to log_stream
                    if capture_output:
                        log_stream.write(content + "\n")
                    else:
                        print(content)
                    log_info("------------------------------------")
                    log_info("✅ Plan generated successfully.")

                    output = log_stream.getvalue() if capture_output else ""
                    return True, output
                else:
                    msg = "\n❌ Agent finished but did not produce a plan (feature_list.json)."
                    log_error(msg)
                    return False, (log_stream.getvalue() if capture_output else "")
            else:
                msg = "\n❌ Agent failed to generate a plan."
                log_error(msg)
                return False, (log_stream.getvalue() if capture_output else "")

        except Exception as e:
            msg = f"Fatal error during planning: {e}"
            log_error(msg)
            if verbose:
                import traceback
                traceback.print_exc()
            return False, (log_stream.getvalue() if capture_output else "")

    finally:
        # Cleanup logger handler to prevent leaks in TUI
        if capture_output and logger_handler:
            logger.removeHandler(logger_handler)
            logger_handler.close()
