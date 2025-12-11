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
from shared.utils import get_file_tree, process_response_blocks, log_startup_config
from shared.agent_client import AgentClient
from .prompts import get_initializer_prompt, get_coding_prompt, get_manager_prompt, copy_spec_to_project

logger = logging.getLogger(__name__)


class CursorClient:
    """Handles interactions with the Cursor Agent CLI."""

    def __init__(self, config: Config):
        self.config = config
        self.agent_client: Optional[Any] = None

    async def run_command(self, prompt: str, cwd: Path,
                          status_callback=None) -> Dict[str, Any]:
        """
        Run a cursor-agent CLI command and return the parsed JSON output.
        """
        logger.debug("Starting cursor-agent subprocess...")

        if self.config.verify_creation:
            logger.info("VERIFICATION MODE: Returning mock response.")
            mock_content = {
                "London": 45.0,
                "New York": 25.0,
                "Paris": 30.0,
                "Tokyo": 100.0
            }
            # Cursor agent typically returns a flat 'content' or 'response' in some wrappers,
            # or simply text in 'text'. Let's match the parsing logic: 'candidates' -> 'content' -> 'parts' -> 'text'
            # OR 'content' key.
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"I will create the output.json file.\n```write:output.json\n{json.dumps(mock_content, indent=4)}\n```"
                        }
                    }
                ],
                # Our parser handles "candidates" or "content".
                # Let's provide "content" directly for simplicity as per
                # agent.py logic line 178
                "content": f"I will create the output.json file.\n```write:output.json\n{json.dumps(mock_content, indent=4)}\n```"
            }

        # Build command
        # cursor-agent agent [prompt] --print --output-format json --force --workspace [cwd]
        # Build command
        # cursor-agent agent [prompt] --print --output-format text --force
        # --workspace [cwd]
        cmd = [
            "cursor-agent", "agent",
            prompt,
            "--print",
            "--output-format", "text",
            "--force",
            "--workspace", str(cwd.resolve())
        ]

        if self.config.model:
            cmd.extend(["--model", self.config.model])

        env = os.environ.copy()
        env["NO_OPEN_BROWSER"] = "1"

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
        except FileNotFoundError:
            logger.error(
                "Cursor Agent CLI not found. Please ensure 'cursor-agent' is installed and in your PATH.")
            raise

        import sys

        logger.debug("Waiting for output...")

        try:
            # Helper for streaming interaction
            async def _read_stream(stream, callback, buffer_list):
                while True:
                    line = await stream.readline()
                    if line:
                        decoded = line.decode()
                        if callback:
                            callback(decoded)
                        buffer_list.append(decoded)
                    else:
                        break

            stdout_buf: List[str] = []
            stderr_buf: List[str] = []

            # Helper callbacks
            def on_stdout(text):
                if self.config.stream_output:
                    sys.stdout.write(text)
                    sys.stdout.flush()
                if status_callback:
                    # We can't send every chunk, but maybe every line or periodically?
                    # For now let's just show we are alive.
                    # Use a non-blocking way if possible, or simple check?
                    # Since this is a callback, we can't easily throttle without state.
                    # But we can just send "Generating..." and rely on the server/client loop to handle it or debounce.
                    # Actually better to just set a flag or update a counter in the outer scope?
                    # Let's just call it. The report_state is threaded/async?
                    # agent_client.report_state uses a thread executor.
                    status_callback("Cursor Generating...")

            def on_stderr(text):
                if self.config.stream_output:
                    sys.stderr.write(text)
                    sys.stderr.flush()

            # Create tasks
            tasks = [
                asyncio.create_task(_read_stream(
                    process.stdout, on_stdout, stdout_buf)),
                asyncio.create_task(_read_stream(
                    process.stderr, on_stderr, stderr_buf))
            ]

            timeout = self.config.timeout

            while True:
                done, pending = await asyncio.wait(tasks, timeout=timeout)

                if not pending:
                    break

                # Check for activity (files or output)
                from shared.utils import has_recent_activity

                # We can also check if our buffers are growing?
                # But has_recent_activity checks filesystem.

                if has_recent_activity(self.config.project_dir, seconds=60):
                    logger.info(
                        "Agent timeout exceeded, but file activity detected. Extending wait by 60s...")
                    status_callback(
                        "Waiting (File Activity Detected)...") if status_callback else None
                    timeout = 60.0
                    continue
                else:
                    logger.error(
                        f"Cursor Agent CLI timed out ({self.config.timeout}s) and no recent file activity.")
                    process.kill()
                    raise asyncio.TimeoutError

            await process.wait()
            stdout = "".join(stdout_buf).encode()
            stderr = "".join(stderr_buf).encode()

            if process.returncode != 0:
                logger.error(
                    f"Cursor process exited with code {process.returncode}")
                if stderr:
                    logger.error(f"STDERR: {stderr.decode()}")

        except Exception as e:
            logger.exception(f"Unexpected error running Cursor Agent: {e}")
            raise

        stdout_text = stdout.decode().strip()
        stderr_text = stderr.decode().strip()

        if self.config.verbose and stderr_text:
            logger.debug(f"Cursor STDERR: {stderr_text}")

        # In TEXT mode, raw stdout is content
        return {"content": stdout_text}

        # JSON parsing logic removed


def print_session_header(iteration: int, is_first: bool) -> None:
    header = f"  SESSION {iteration} " + \
        ("(INITIALIZATION)" if is_first else "(CODING)")
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
    recent_history: List[str] = []
) -> tuple[str, str, List[str]]:
    """
    Run a single agent session using Cursor CLI.
    """
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
                if passing == total:
                    feature_status = f"Feature List Status: ALL {total}/{total} FEATURES PASSING. Project is verified complete."
                else:
                    feature_status = f"Feature List Status: {passing}/{total} passing. You are NOT done until {total}/{total} pass."
            except Exception as e:
                feature_status = f"Feature List Status: Error reading file ({e})"

        history_text = "\n".join(
            [f"- {h}" for h in recent_history]) if recent_history else "None"
        context_block = f"""
CURRENT CONTEXT:
Working Directory: {client.config.project_dir}
{feature_status}
RECENT ACTIONS:
{history_text}

{file_tree}
"""
        # We append a reminder to use the code block format and tool usage
        augmented_prompt = prompt + \
            f"\n{context_block}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search."

        # Define callback to update dashboard status
        def status_update(msg):
            if client.agent_client:
                client.agent_client.report_state(current_task=msg)

        if client.agent_client:
            client.agent_client.report_state(
                current_task="Sending Prompt to Agent")

            # Also recover logs if they are empty from a restart?
            # No, we can't easily recover history from disk here without parsing logs.
            # But we can at least show we are starting.

        logger.debug(f"Sending Augmented Prompt:\n{augmented_prompt}")

        result = await client.run_command(
            augmented_prompt,
            client.config.project_dir,
            status_callback=status_update
        )

        response_text = ""
        # Handle result structure from Cursor API
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
            logger.info("Received response from Cursor Agent.")
            if client.agent_client:
                client.agent_client.report_state(
                    current_task="Processing Response")
            # Only log full response in debug
            logger.debug(f"Response:\n{response_text}")
        else:
            logger.warning("No text content found in Cursor response.")
            logger.info(
                f"Full Cursor response: {json.dumps(result, indent=2)}")

        # Execute any blocks found in the response
        executed_actions = []
        if response_text:
            logger.info("Processing response blocks...")

            # Define callback to update dashboard status
            def status_update(msg):
                if client.agent_client:
                    client.agent_client.report_state(current_task=msg)

            log, actions = await process_response_blocks(
                response_text,
                client.config.project_dir,
                client.config.bash_timeout,
                status_callback=status_update
            )

            if log:
                logger.info("Execution Log updated.")
                # We do NOT report the full execution log to the dashboard to avoid overwriting history
                # if client.agent_client:
                #    client.agent_client.report_state(last_log=[f"Execution Log:\n{log}"])
            executed_actions = actions

        return "continue", response_text, executed_actions

        return "continue", response_text

    except Exception as e:
        logger.exception("Error during agent session")
        # Do not overwrite history with error
        if client.agent_client:
            client.agent_client.report_state(current_task=f"Error: {e}")
        return "error", str(e), []


async def run_autonomous_agent(
        config: Config,
        agent_client: Optional[AgentClient] = None) -> None:
    """
    Run the autonomous agent loop.
    """
    log_startup_config(config, logger)

    # Create project directory
    config.project_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Client
    client = CursorClient(config)
    # Store agent client on cursor client if we wanted to pass it down deeper,
    # but for now we keep it local or attached to client for easier access in run_agent_session if we passed it there.
    # Let's attach it to CursorClient for convenience if we refactor run_agent_session to use it,
    # BUT run_agent_session takes client.
    setattr(client, "agent_client", agent_client)

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

    # Mark as running
    if agent_client:
        agent_client.report_state(is_running=True, current_task="Initializing")

    while True:
        # Check Control State
        if agent_client:
            ctl = agent_client.poll_commands()

            if ctl.stop_requested:
                logger.info("Stop requested by user.")
                # Report stop before breaking
                agent_client.report_state(
                    is_running=False, current_task="Stopped")
                break

            if ctl.pause_requested:
                agent_client.report_state(
                    is_paused=True, current_task="Paused")
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
                iteration=iteration, current_task="Preparing Prompt")

        if config.max_iterations and iteration > config.max_iterations:
            logger.info(f"\nReached max iterations ({config.max_iterations})")
            break

        if (config.project_dir / "COMPLETED").exists():
            logger.info("\n" + "=" * 50)
            logger.info("  PROJECT COMPLETED (Found COMPLETED file)")
            logger.info("=" * 50)
            break

        print_session_header(iteration, is_first_run)

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
                logger.info(
                    f"Manager triggered by frequency (Iteration {iteration}).")
                should_run_manager = True

            if should_run_manager:
                prompt = get_manager_prompt()
                using_manager = True
            else:
                prompt = get_coding_prompt()

        # Run session
        if agent_client:
            agent_client.report_state(
                current_task=f"Executing {
                    'Manager' if using_manager else 'Agent'}")

        original_model = config.model
        if using_manager and config.manager_model:
            config.model = config.manager_model
            logger.info(f"Switched to Manager Model: {config.model}")

        status, response, new_actions = await run_agent_session(client, prompt, recent_history)

        if using_manager and config.manager_model:
            config.model = original_model
            logger.info(f"Restored Agent Model: {config.model}")

        if new_actions:
            recent_history.extend(new_actions)
            recent_history = recent_history[-10:]  # Keep last 10 actions
            if agent_client:
                agent_client.report_state(
                    last_log=[str(a) for a in recent_history])

        if status == "continue":
            consecutive_errors = 0
            is_first_run = False  # Successful run, next run is coding

            if agent_client:
                agent_client.report_state(
                    current_task="Waiting (Auto-Continue)")

            logger.info(
                f"Agent will auto-continue in {config.auto_continue_delay}s...")
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
                f"Session encountered an error (Attempt {consecutive_errors}/{
                    config.max_consecutive_errors}).")

            if consecutive_errors >= config.max_consecutive_errors:
                logger.critical(
                    f"Too many consecutive errors ({
                        config.max_consecutive_errors}). Stopping execution.")
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
