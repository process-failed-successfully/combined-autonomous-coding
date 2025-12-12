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
from shared.utils import get_file_tree, process_response_blocks, log_startup_config, log_system_health
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

        # Create a filtered environment to avoid hitting ARG_MAX on macOS
        # We start with a clean dict and copy only essential or safe variables
        env = {}
        safe_keys = {
            "PATH", "HOME", "USER", "SHELL", "TERM", "TMPDIR",
            "LANG", "LC_ALL", "LC_CTYPE", "DISPLAY", "XAUTHORITY",
            "SSH_AUTH_SOCK", "SSH_AGENT_PID",
            "WORKSPACE_DIR", "PROJECT_NAME",
             # Node/NPM related
            "NODE_ENV", "NVM_DIR"
        }

        for k, v in os.environ.items():
            if k in safe_keys or k.startswith("CURSOR_") or k.startswith("XDG_") or k.startswith("npm_"):
                env[k] = v

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
                    # Stream output to status callback
                    # We pass current_task to ensure the user knows it's active
                    status_callback(current_task="Cursor Generating...", output_line=text)

            def on_stderr(text):
                # Always log stderr to debug/info for visibility
                if text.strip():
                    logger.warning(f"Cursor Agent STDERR: {text.strip()}")
                
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

            timeout_counter = self.config.timeout
            last_stdout_len = 0
            last_stderr_len = 0

            while True:
                # Wait for a short interval to check activity
                # We use a shorter wait here to frequently check for output flow
                done, pending = await asyncio.wait(tasks, timeout=5.0)

                if not pending:
                    break

                # Check for Output Activity (Streaming)
                current_stdout_len = len(stdout_buf)
                current_stderr_len = len(stderr_buf)

                if current_stdout_len > last_stdout_len or current_stderr_len > last_stderr_len:
                    # We have activity! Reset timeout counter
                    # But we don't reset the *loop* timeout, we just don't decrement the counter
                    # Actually, we should probably implement a custom timeout counter since asyncio.wait argument is a max wait.
                    # Let's simplify: execution continues as long as we have output OR file activity.
                    timeout_counter = self.config.timeout
                    last_stdout_len = current_stdout_len
                    last_stderr_len = current_stderr_len
                    continue
                
                # No output activity this interval. Decrement counter.
                timeout_counter -= 5.0

                if timeout_counter > 0:
                    continue

                # Timeout exceeded? Check file activity as last resort.
                from shared.utils import has_recent_activity
                if has_recent_activity(self.config.project_dir, seconds=60):
                    logger.info(
                        "Agent timeout exceeded, but file activity detected. Extending wait by 60s...")
                    status_callback(
                        "Waiting (File Activity Detected)...") if status_callback else None
                    timeout_counter = 60.0
                    continue
                else:
                    logger.error(
                        f"Cursor Agent CLI timed out ({self.config.timeout}s) and no recent output or file activity.")
                    process.kill()
                    raise asyncio.TimeoutError

            await process.wait()
            stdout = "".join(stdout_buf).encode()
            stderr = "".join(stderr_buf).encode()

            if process.returncode != 0:
                error_msg = f"Cursor process exited with code {process.returncode}"
                logger.error(error_msg)
                
                if stderr:
                    logger.error(f"STDERR: {stderr.decode()}")

                # Special handling for SIGTERM (143) to identify it clearly
                if process.returncode == 143 or process.returncode == -15:
                    health_info = log_system_health()
                    raise Exception(f"Cursor Agent received SIGTERM (Exit 143). This may be due to OOM or external termination. {health_info} {error_msg}")
                
                # For other errors, we also raise so the agent loop can retry
                raise Exception(error_msg)

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
    recent_history: List[str] = [],
    status_callback: Optional[Any] = None,
    metrics_callback: Optional[Any] = None
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
                if metrics_callback:
                    metrics_callback("feature_stats", {"count": passing, "pct": pct})

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

        # Truncation Logic to avoid ARG_MAX and reduce crash risk
        MAX_PROMPT_CHARS = 100000
        if len(augmented_prompt) > MAX_PROMPT_CHARS:
            logger.warning(f"Prompt length ({len(augmented_prompt)}) exceeds limit ({MAX_PROMPT_CHARS}). Truncating context.")
            
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
            augmented_prompt = prompt + \
                f"\n{context_block}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search."
            
            # 2. If still too long, truncate recent history
            if len(augmented_prompt) > MAX_PROMPT_CHARS:
                short_history_text = "\n".join([f"- {h}" for h in recent_history[-2:]]) if recent_history else "None"
                
                context_block = f"""
CURRENT CONTEXT:
Working Directory: {client.config.project_dir}
{feature_status}
RECENT ACTIONS:
{short_history_text}

{truncated_file_tree}
"""
                augmented_prompt = prompt + \
                    f"\n{context_block}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search."

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
            client.agent_client.report_state(
                current_task="Sending Prompt to Agent")

        logger.debug(f"Sending Augmented Prompt:\n{augmented_prompt}")

        # Measure LLM Latency
        start_time = time.time()
        result = await client.run_command(
            augmented_prompt,
            client.config.project_dir,
            status_callback=local_status_update
        )
        latency = time.time() - start_time
        if metrics_callback:
            metrics_callback("llm_latency", latency)

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
            def block_status_update(msg):
                local_status_update(current_task=msg)

            log, actions = await process_response_blocks(
                response_text,
                client.config.project_dir,
                client.config.bash_timeout,
                status_callback=block_status_update,
                metrics_callback=metrics_callback
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
        config: Config,
        agent_client: Optional[AgentClient] = None) -> None:
    """
    Run the autonomous agent loop.
    """
    import time
    log_startup_config(config, logger)

    # Create project directory
    config.project_dir.mkdir(parents=True, exist_ok=True)

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

    # Metrics Callback Handler
    def handle_metrics(metric_type: str, value: Any):
        if not agent_client:
            return
            
        updates = {}
        
        if metric_type.startswith("tool:"):
            tool_name = metric_type.split(":")[1]
            updates["tool_usage_delta"] = {tool_name: value}
            
        elif metric_type == "error":
            updates["error_match"] = True
            
        elif metric_type == "feature_stats":
            updates["feature_completion_count"] = value["count"]
            updates["feature_completion_pct"] = value["pct"]
            
        elif metric_type == "llm_latency":
            metrics_state["llm_latencies"].append(value)
            avg = sum(metrics_state["llm_latencies"]) / len(metrics_state["llm_latencies"])
            updates["avg_llm_latency"] = avg
            
        elif metric_type == "execution_time":
            metrics_state["tool_times"].append(value)
            avg = sum(metrics_state["tool_times"]) / len(metrics_state["tool_times"])
            updates["avg_tool_execution_time"] = avg
            
        if updates:
            agent_client.report_state(**updates)

    # Mark as running
    if agent_client:
        agent_client.report_state(
            is_running=True, 
            current_task="Initializing",
            start_time=start_time
        )

    while True:
        iter_start_time = time.time()
        
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

        if (config.project_dir / "PROJECT_SIGNED_OFF").exists():
            logger.info("\n" + "=" * 50)
            logger.info("  PROJECT SIGNED OFF")
            logger.info("=" * 50)
            break

        if (config.project_dir / "COMPLETED").exists():
            logger.info("Project marks as COMPLETED but missing SIGN-OFF. Triggering Manager...")
            should_run_manager = True
            
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
                logger.info(
                    f"Manager triggered by frequency (Iteration {iteration}).")
                should_run_manager = True

            # Auto-trigger Manager if all features are passing
            if not should_run_manager and config.feature_list_path.exists():
                try:
                    features = json.loads(config.feature_list_path.read_text())
                    total = len(features)
                    passing = sum(1 for f in features if f.get("passes", False))
                    if total > 0 and passing == total:
                        logger.info("All features passed. Triggering Manager for potential sign-off.")
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
                current_task=f"Executing {'Manager' if using_manager else 'Agent'}")

        original_model = config.model
        if using_manager and config.manager_model:
            config.model = config.manager_model
            logger.info(f"Switched to Manager Model: {config.model}")

        status, response, new_actions = await run_agent_session(
            client, 
            prompt, 
            recent_history,
            metrics_callback=handle_metrics
        )

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
            
            # Calculate Iteration Time & Update Averages
            iter_duration = time.time() - iter_start_time
            metrics_state["iteration_times"].append(iter_duration)
            avg_iter = sum(metrics_state["iteration_times"]) / len(metrics_state["iteration_times"])
            
            if agent_client:
                agent_client.report_state(avg_iteration_time=avg_iter)

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
                f"Session encountered an error (Attempt {consecutive_errors}/{config.max_consecutive_errors}).")

            if consecutive_errors >= config.max_consecutive_errors:
                logger.critical(
                    f"Too many consecutive errors ({config.max_consecutive_errors}). Stopping execution.")
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
