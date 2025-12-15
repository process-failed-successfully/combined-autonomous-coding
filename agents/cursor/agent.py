"""
Cursor Agent Session Logic
==========================

Core agent interaction functions for running autonomous coding sessions using Cursor CLI.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional, Any, Dict, List

from shared.config import Config
from shared.utils import (
    get_file_tree,
    process_response_blocks,
    log_startup_config,
    log_system_health,
)
from shared.agent_client import AgentClient
from shared.telemetry import init_telemetry, get_telemetry
from .prompts import (
    get_initializer_prompt,
    get_coding_prompt,
    get_manager_prompt,
    copy_spec_to_project,
)

logger = logging.getLogger(__name__)


from .client import CursorClient


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
    client: CursorClient,
    prompt: str,
    recent_history: List[str] = [],
    status_callback: Optional[Any] = None,
    metrics_callback: Optional[Any] = None,
) -> tuple[str, str, List[str]]:
    """
    Run a single agent session using Cursor CLI.
    """
    import time

    logger.info("Sending prompt to Cursor Agent...")

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

        # Truncation Logic to avoid ARG_MAX and reduce crash risk
        MAX_PROMPT_CHARS = 100000
        if len(augmented_prompt) > MAX_PROMPT_CHARS:
            logger.warning(
                f"Prompt length ({len(augmented_prompt)}) exceeds limit ({MAX_PROMPT_CHARS}). Truncating context."
            )

            # 1. Truncate File Tree
            truncated_file_tree = file_tree[:5000] + "\n... (File tree truncated)"

            context_block = f"""
CURRENT CONTEXT:
Working Directory: {client.config.project_dir}
{feature_status}
RECENT ACTIONS:
{history_text}

{truncated_file_tree}
"""
            augmented_prompt = (
                prompt
                + f"\n{context_block}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search."
            )

            # 2. If still too long, truncate recent history
            if len(augmented_prompt) > MAX_PROMPT_CHARS:
                short_history_text = (
                    "\n".join([f"- {h}" for h in recent_history[-2:]])
                    if recent_history
                    else "None"
                )

                context_block = f"""
CURRENT CONTEXT:
Working Directory: {client.config.project_dir}
{feature_status}
RECENT ACTIONS:
{short_history_text}

{truncated_file_tree}
"""
                augmented_prompt = (
                    prompt
                    + f"\n{context_block}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search."
                )

        # Define callback to update dashboard status
        current_turn_log = []

        def local_status_update(current_task=None, output_line=None):
            # If an external callback is provided, call it
            if status_callback:
                status_callback(current_task=current_task, output_line=output_line)

            # Also perform local logic (Dashboard Client specific)
            if not client.agent_client:
                return

            updates = {}
            if current_task:
                updates["current_task"] = current_task

            if output_line:
                clean_line = output_line.rstrip()
                if clean_line:
                    current_turn_log.append(clean_line)
                    updates["last_log"] = current_turn_log[-30:]

            client.agent_client.report_state(**updates)

        if client.agent_client:
            client.agent_client.report_state(current_task="Sending Prompt to Agent")

        logger.debug(f"Sending Augmented Prompt:\n{augmented_prompt}")

        # Measure LLM Latency
        start_time = time.time()
        result = await client.run_command(
            augmented_prompt,
            client.config.project_dir,
            status_callback=local_status_update,
        )
        latency = time.time() - start_time
        latency = time.time() - start_time
        get_telemetry().record_histogram(
            "llm_latency_seconds",
            latency,
            labels={"model": client.config.model, "operation": "generate_content"},
        )

        response_text = ""
        # Handle result structure from Cursor API
        if "candidates" in result:
            for candidate in result["candidates"]:
                for part in candidate.get("content", {}).get("parts", []):
                    if "text" in part:
                        response_text += part["text"]
        elif "content" in result:
            response_text = result.get("content", "")
        elif "response" in result:
            response_text = result.get("response", "")
        else:
            if result:
                logger.debug(f"Full result keys: {result.keys()}")

        if response_text:
            logger.info("Received response from Cursor Agent.")
            if client.agent_client:
                client.agent_client.report_state(current_task="Processing Response")
            # Only log full response in debug
            logger.debug(f"Response:\n{response_text}")
        else:
            logger.warning("No text content found in Cursor response.")
            logger.info(f"Full Cursor response: {json.dumps(result, indent=2)}")

        # Record Token Usage if available
        if "usageMetadata" in result:
            usage = result["usageMetadata"]
            prompt_tokens = usage.get("promptTokenCount", 0)
            candidates_tokens = usage.get("candidatesTokenCount", 0)
            total_tokens = usage.get("totalTokenCount", 0)

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

        # Execute any blocks found in the response
        executed_actions = []
        if response_text:
            logger.info("Processing response blocks...")

            # Define callback to update dashboard status
            def block_status_update(msg):
                local_status_update(current_task=msg)

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
        # Do not overwrite history with error
        if client.agent_client:
            client.agent_client.report_state(current_task=f"Error: {e}")
        return "error", str(e), []


async def run_autonomous_agent(
    config: Config, agent_client: Optional[AgentClient] = None
) -> None:
    """
    Run the autonomous agent loop.
    """
    import time

    log_startup_config(config, logger)

    # Create project directory
    config.project_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Telemetry
    # Use agent_id from client if available
    service_name = "cursor_agent"
    if agent_client:
        service_name = agent_client.agent_id

    init_telemetry(
        service_name, agent_type="cursor", project_name=config.project_dir.name
    )
    get_telemetry().start_system_monitoring()

    # Initialize Client
    client = CursorClient(config)
    setattr(client, "agent_client", agent_client)

    # Login Mode
    if config.login_mode:
        logger.info("Starting Cursor Login Flow...")
        import subprocess

        try:
            subprocess.run(["cursor-agent", "login"], check=False)
        except FileNotFoundError:
            logger.error("Cursor Agent CLI not found.")
        except Exception as e:
            logger.error(f"Error during login: {e}")
        return

    # Check state
    is_first_run = not config.feature_list_path.exists()

    if is_first_run:
        logger.info("Fresh start - will use initializer agent")
        logger.info("This may create the initial spec. Please wait.")
        copy_spec_to_project(config.project_dir, config.spec_file)
    else:
        logger.info("Continuing existing project")
        log_progress_summary(config.project_dir, config.progress_file_path)

    iteration = 0
    consecutive_errors = 0
    recent_history: List[str] = []
    has_run_manager_first = False
    start_time = time.time()

    # Session Metrics State
    metrics_state = {
        "llm_latencies": [],
        "tool_times": [],
        "iteration_times": [],
    }

    # Metrics Callback Handler (REMOVED - Use Telemetry)
    # def handle_metrics(metric_type: str, value: Any): ...

    # Mark as running
    if agent_client:
        agent_client.report_state(
            is_running=True, current_task="Initializing", start_time=start_time
        )

    while True:
        iter_start_time = time.time()

        # Check Control State
        if agent_client:
            ctl = agent_client.poll_commands()

            if ctl.stop_requested:
                logger.info("Stop requested by user.")
                # Report stop before breaking
                agent_client.report_state(is_running=False, current_task="Stopped")
                break

            if ctl.pause_requested:
                agent_client.report_state(is_paused=True, current_task="Paused")
                logger.info("Agent Paused. Waiting for resume...")
                while True:
                    await asyncio.sleep(1)
                    ctl = agent_client.poll_commands()
                    if ctl.stop_requested:
                        return
                    if not ctl.pause_requested:
                        break
                agent_client.report_state(is_paused=False)
                logger.info("Agent Resumed.")

            if ctl.skip_requested:
                agent_client.clear_skip()
                logger.info("Skipping iteration as requested.")
                continue

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

            logger.info(
                "Project marks as COMPLETED but missing SIGN-OFF. Triggering Manager..."
            )
            should_run_manager = True

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
        using_manager = False

        if is_first_run:
            prompt = get_initializer_prompt()
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

        status, response, new_actions = await run_agent_session(
            client, prompt, recent_history, metrics_callback=None  # Deprecated
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

            # Calculate Iteration Time & Update Averages
            iter_duration = time.time() - iter_start_time
            # metrics_state["iteration_times"].append(iter_duration) # REMOVED
            # avg_iter = sum(metrics_state["iteration_times"]) / len(metrics_state["iteration_times"]) # REMOVED

            # Telemetry: Record Iteration Duration
            get_telemetry().record_gauge("iteration_duration_seconds", iter_duration)

            if agent_client:
                # agent_client.report_state(avg_iteration_time=avg_iter) # Deprecated
                pass

            logger.info(f"Agent will auto-continue in {config.auto_continue_delay}s...")
            log_progress_summary(config.project_dir, config.progress_file_path)

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

    if agent_client:
        agent_client.report_state(is_running=False, current_task="Completed")
