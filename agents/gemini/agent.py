"""
Gemini Agent Session Logic
==========================

Core agent interaction functions for running autonomous coding sessions using Gemini CLI.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Any, List

from shared.config import Config
from shared.utils import get_file_tree, process_response_blocks, log_startup_config
from shared.telemetry import init_telemetry, get_telemetry
from .prompts import (
    get_initializer_prompt,
    get_coding_prompt,
    get_manager_prompt,
    copy_spec_to_project,
)
from .client import GeminiClient


logger = logging.getLogger(__name__)


def print_session_header(iteration: int, is_first: bool) -> None:
    header = f"  SESSION {iteration} " + (
        "(INITIALIZATION)" if is_first else "(CODING)"
    )
    logger.info("\n" + "=" * 50)
    logger.info(header)
    logger.info("=" * 50 + "\n")


def log_progress_summary(project_dir: Path, progress_file: Path) -> None:
    if progress_file.exists():
        logger.info("Last Progress Update:")
        logger.info("-" * 30)
        # Read last 5 lines
        try:
            lines = progress_file.read_text().splitlines()
            for line in lines[-10:]:
                logger.info(line)
        except Exception as e:
            logger.warning(f"Could not read progress file: {e}")
        logger.info("-" * 30 + "\n")


async def run_agent_session(
    client: GeminiClient,
    prompt: str,
    recent_history: List[str] = [],
    status_callback: Optional[Any] = None,
    metrics_callback: Optional[Any] = None,
) -> tuple[str, str, List[str]]:
    """
    Run a single agent session using Gemini CLI.
    """
    import time

    logger.info("Sending prompt to Gemini...")

    try:
        # INJECT DYNAMIC CONTEXT
        file_tree = get_file_tree(client.config.project_dir)

        # INJECT REALITY CHECK
        feature_status = "Feature List Status: Not found"
        feature_file = client.config.feature_list_path
        if feature_file.exists():
            try:
                features = json.loads(feature_file.read_text())
                total = len(features)
                passing = sum(1 for f in features if f.get("passes", False))
                if total > 0:
                    pct = (passing / total) * 100.0
                else:
                    pct = 0.0

                # Report Feature Metrics
                get_telemetry().record_gauge("feature_completion_count", passing)
                get_telemetry().record_gauge("feature_completion_pct", pct)

                if passing == total:
                    feature_status = f"Feature List Status: ALL {total}/{total} FEATURES PASSING. Project is verified complete."
                else:
                    feature_status = f"Feature List Status: {passing}/{total} passing. You are NOT done until {total}/{total} pass."
            except Exception as e:
                feature_status = f"Feature List Status: Error reading file ({e})"

        history_text = (
            "\n".join([f"- {h}" for h in recent_history]) if recent_history else "None"
        )
        context_block = f"""
CURRENT CONTEXT:
Working Directory: {client.config.project_dir}
{feature_status}
RECENT ACTIONS:
{history_text}

{file_tree}
"""
        # We append a reminder to use the code block format and tool usage
        augmented_prompt = (
            prompt
            + f"\n{context_block}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search."
        )

        logger.debug(f"Sending Augmented Prompt:\n{augmented_prompt}")

        # Measure LLM Latency
        start_time = time.time()

        # Define callback to update dashboard status (aligns with Cursor
        # parity)
        def local_status_update(current_task=None, output_line=None):
            if status_callback:
                status_callback(current_task=current_task, output_line=output_line)

        result = await client.run_command(
            augmented_prompt,
            client.config.project_dir,
            status_callback=local_status_update,
        )
        latency = time.time() - start_time
        get_telemetry().record_histogram(
            "llm_latency_seconds",
            latency,
            labels={"model": client.config.model, "operation": "generate_content"},
        )

        response_text = ""
        # Handle 'candidates' structure from Gemini API
        if "candidates" in result:
            for candidate in result["candidates"]:
                for part in candidate.get("content", {}).get("parts", []):
                    if "text" in part:
                        response_text += part["text"]
        # Handle flattened 'content' (some CLI wrappers do this)
        elif "content" in result:
            response_text = result.get("content", "")
        # Handle 'response' key (observed in some CLI versions)
        elif "response" in result:
            response_text = result.get("response", "")
        else:
            if result:
                logger.debug(f"Full result keys: {result.keys()}")

        if response_text:
            logger.info("Received response from Gemini.")
            # Only log full response in debug
            logger.debug(f"Response:\n{response_text}")
        else:
            logger.warning("No text content found in Gemini response.")
            logger.info(f"Full Gemini response: {json.dumps(result, indent=2)}")

            # Record Token Usage if available
        if "usageMetadata" in result:
            usage = result["usageMetadata"]
            prompt_tokens = usage.get("promptTokenCount", 0)
            candidates_tokens = usage.get("candidatesTokenCount", 0)
            # _total_tokens = usage.get("totalTokenCount", 0)

            get_telemetry().increment_counter(
                "llm_tokens_total",
                prompt_tokens,
                labels={"model": client.config.model, "type": "input"},
            )
            get_telemetry().increment_counter(
                "llm_tokens_total",
                candidates_tokens,
                labels={"model": client.config.model, "type": "output"},
            )

        # Detailed diagnostics
        if "promptFeedback" in result:
            logger.warning(
                f"Prompt Feedback: {json.dumps(result['promptFeedback'], indent=2)}"
            )

        if "candidates" in result:
            for i, candidate in enumerate(result["candidates"]):
                finish_reason = candidate.get("finishReason")
                if finish_reason:
                    logger.warning(f"Candidate {i} finish reason: {finish_reason}")

                safety_ratings = candidate.get("safetyRatings")
                if safety_ratings:
                    logger.warning(
                        f"Candidate {i} safety ratings: {json.dumps(safety_ratings, indent=2)}"
                    )

        # Execute any blocks found in the response
        executed_actions = []
        if response_text:
            logger.info("Processing response blocks...")

            # Wrapper for process_response_blocks to match expected signature
            def block_status_update(msg):
                if status_callback:
                    status_callback(current_task=msg)

            log, actions = await process_response_blocks(
                response_text,
                client.config.project_dir,
                client.config.bash_timeout,
                status_callback=block_status_update,
            )
            if log:
                logger.info("Execution Log updated.")
            executed_actions = actions

        return "continue", response_text, executed_actions

    except Exception as e:
        logger.exception("Error during agent session")
        return "error", str(e), []


async def run_autonomous_agent(  # noqa: C901
    config: Config, agent_client: Optional[Any] = None
):  # noqa: C901
    """
    Run the autonomous agent loop.
    """
    import time

    log_startup_config(config, logger)

    # Initialize Telemetry
    # Use agent_id from client if available, ensuring metrics match the
    # generated ID
    service_name = "gemini_agent"
    if agent_client:
        service_name = agent_client.agent_id

    init_telemetry(
        service_name, agent_type="gemini", project_name=config.project_dir.name
    )
    get_telemetry().start_system_monitoring()
    get_telemetry().capture_logs_from("agents")

    client = GeminiClient(config)

    # Load Prompts
    # Load Prompts (Pre-load to ensure they exist)
    _ = get_initializer_prompt()
    _ = get_coding_prompt()
    _ = get_manager_prompt()

    # Session State
    recent_history: List[str] = []
    iteration = 0
    start_time = time.time()

    # Initialize State
    is_first_run = not config.feature_list_path.exists()
    has_run_manager_first = False

    # Initialize Project (Copy Spec)
    copy_spec_to_project(config.project_dir, config.spec_file)

    # Metrics Callback Handler (REMOVED - Use Telemetry)
    # def handle_metrics(metric_type: str, value: Any): ...

    # Initial Status
    if agent_client:
        agent_client.report_state(
            current_task="Initializing", is_running=True, start_time=start_time
        )

    # Main Loop
    while True:
        iter_start_time = time.time()

        # Check Limits
        if config.max_iterations and iteration >= config.max_iterations:
            logger.info("Max iterations reached. Stopping.")
            break

        # Check Control Signals
        if agent_client:
            control = agent_client.poll_commands()
            if control.stop_requested:
                logger.info("Stop requested by user.")
                break
            if control.pause_requested:
                agent_client.report_state(current_task="Paused", is_paused=True)
                while control.pause_requested:
                    await asyncio.sleep(1)
                    control = agent_client.poll_commands()
                    if control.stop_requested:
                        return
                agent_client.report_state(current_task="Resuming...", is_paused=False)

        iteration += 1
        # Update State
        if agent_client:
            agent_client.report_state(
                iteration=iteration, current_task="Preparing Prompt"
            )

        # Telemetry: Record Iteration
        get_telemetry().record_gauge("agent_iteration", iteration)
        get_telemetry().increment_counter("agent_iterations_total")

        if config.max_iterations and iteration > config.max_iterations:
            logger.info(f"\nReached max iterations ({config.max_iterations})")
            break

        if (config.project_dir / "PROJECT_SIGNED_OFF").exists():
            logger.info("\n" + "=" * 50)
            logger.info("  PROJECT SIGNED OFF")
            logger.info("=" * 50)
            break

        if (config.project_dir / "COMPLETED").exists():
            logger.info(
                "Project marks as COMPLETED but missing SIGN-OFF. Triggering Manager..."
            )
            should_run_manager = True
            # Ensure we force manager execution in the next block logic
            # (The logic below handles `should_run_manager`, but we need to ensure we don't skip it)

        # Check for Human in Loop
        human_loop_file = config.project_dir / "human_in_loop.txt"
        if human_loop_file.exists():
            try:
                reason = human_loop_file.read_text().strip()
                logger.info("\n" + "=" * 50)
                logger.info("  HUMAN IN LOOP REQUESTED")
                logger.info("=" * 50)
                logger.info(f"Reason: {reason}")
                logger.info(
                    "Stopping execution until human intervention is resolved (file removed)."
                )

                if agent_client:
                    agent_client.report_state(
                        is_running=False,
                        current_task=f"Stopped: Human in Loop ({reason})",
                    )
                break
            except Exception as e:
                logger.error(f"Error reading human_in_loop.txt: {e}")

        print_session_header(iteration, is_first_run)

        # Choose prompt
        # Choose prompt
        using_manager = False

        if is_first_run:
            prompt = get_initializer_prompt()
            # Note: We don't flip is_first_run to False until we get a success
        else:
            # Check for Manager Triggers
            should_run_manager = False
            manager_trigger_path = config.project_dir / "TRIGGER_MANAGER"

            if manager_trigger_path.exists():
                logger.info("Manager triggered by TRIGGER_MANAGER file.")
                should_run_manager = True
                try:
                    manager_trigger_path.unlink()
                except OSError:
                    pass
            elif config.run_manager_first and not has_run_manager_first:
                logger.info("Manager triggered by --manager-first flag.")
                should_run_manager = True
                has_run_manager_first = True
            elif iteration > 0 and iteration % config.manager_frequency == 0:
                logger.info(f"Manager triggered by frequency (Iteration {iteration}).")
                should_run_manager = True

            # Auto-trigger Manager if all features are passing
            if not should_run_manager and config.feature_list_path.exists():
                try:
                    features = json.loads(config.feature_list_path.read_text())
                    total = len(features)
                    passing = sum(1 for f in features if f.get("passes", False))
                    if total > 0 and passing == total:
                        logger.info(
                            "All features passed. Triggering Manager for potential sign-off."
                        )
                        should_run_manager = True
                except Exception:
                    pass

            if should_run_manager:
                prompt = get_manager_prompt()
                using_manager = True
            else:
                prompt = get_coding_prompt()

        # Run session
        if agent_client:
            agent_client.report_state(
                current_task=f"Executing {'Manager' if using_manager else 'Agent'}"
            )

        original_model = config.model
        if using_manager and config.manager_model:
            config.model = config.manager_model
            logger.info(f"Switched to Manager Model: {config.model}")

        # Status Callback Handler
        current_turn_log = []

        def status_update(current_task=None, output_line=None):
            if not agent_client:
                return

            updates = {}
            if current_task:
                updates["current_task"] = current_task

            if output_line:
                clean_line = output_line.rstrip()
                if clean_line:
                    current_turn_log.append(clean_line)
                    updates["last_log"] = current_turn_log[-30:]

            if updates:
                agent_client.report_state(**updates)

        status, response, new_actions = await run_agent_session(
            client,
            prompt,
            recent_history,
            status_callback=status_update,
            metrics_callback=None,  # Deprecated
        )

        if using_manager and config.manager_model:
            config.model = original_model
            logger.info(f"Restored Agent Model: {config.model}")

        if new_actions:
            recent_history.extend(new_actions)
            recent_history = recent_history[-10:]  # Keep last 10 actions
            if agent_client:
                agent_client.report_state(last_log=[str(a) for a in recent_history])

        if status == "continue":
            consecutive_errors = 0
            is_first_run = False  # Successful run, next run is coding

            if agent_client:
                agent_client.report_state(current_task="Waiting (Auto-Continue)")

            logger.info(f"Agent will auto-continue in {config.auto_continue_delay}s...")
            log_progress_summary(config.project_dir, config.progress_file_path)

            # Telemetry: Record Iteration Duration
            get_telemetry().record_gauge(
                "iteration_duration_seconds", time.time() - iter_start_time
            )

            # Interruptible sleep
            sleep_steps = int(config.auto_continue_delay * 10)
            for _ in range(sleep_steps):
                await asyncio.sleep(0.1)
                # Check interruption
                if agent_client and agent_client.poll_commands().stop_requested:
                    break

        elif status == "error":
            consecutive_errors += 1
            logger.error(
                f"Session encountered an error (Attempt {consecutive_errors}/{config.max_consecutive_errors})."
            )

            if consecutive_errors >= config.max_consecutive_errors:
                logger.critical(
                    f"Too many consecutive errors ({config.max_consecutive_errors}). Stopping execution."
                )
                break

            logger.info("Retrying in 10 seconds...")
            await asyncio.sleep(10)

        # Prepare next session
        if config.max_iterations is None or iteration < config.max_iterations:
            logger.debug("Preparing next session...")
            await asyncio.sleep(1)

    logger.info("\n" + "=" * 50)
    logger.info("  SESSION COMPLETE")
    logger.info("=" * 50)
