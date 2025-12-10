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
from .prompts import get_initializer_prompt, get_coding_prompt, copy_spec_to_project

logger = logging.getLogger(__name__)


class CursorClient:
    """Handles interactions with the Cursor Agent CLI."""
    
    def __init__(self, config: Config):
        self.config = config

    async def run_command(self, prompt: str, cwd: Path) -> Dict[str, Any]:
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
                # Let's provide "content" directly for simplicity as per agent.py logic line 178
                "content": f"I will create the output.json file.\n```write:output.json\n{json.dumps(mock_content, indent=4)}\n```"
            }
        
        # Build command
        # cursor-agent agent [prompt] --print --output-format json --force --workspace [cwd]
        # Build command
        # cursor-agent agent [prompt] --print --output-format text --force --workspace [cwd]
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
            logger.error("Cursor Agent CLI not found. Please ensure 'cursor-agent' is installed and in your PATH.")
            raise

        import time
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
            
            stdout_buf = []
            stderr_buf = []
            
            # Helper callbacks
            def on_stdout(text):
                if self.config.stream_output:
                    sys.stdout.write(text)
                    sys.stdout.flush()
            
            def on_stderr(text):
                 if self.config.stream_output:
                    sys.stderr.write(text)
                    sys.stderr.flush()

            # Create tasks
            tasks = [
                asyncio.create_task(_read_stream(process.stdout, on_stdout, stdout_buf)),
                asyncio.create_task(_read_stream(process.stderr, on_stderr, stderr_buf))
            ]
            
            timeout = self.config.timeout
            
            while True:
                done, pending = await asyncio.wait(tasks, timeout=timeout)
                
                if not pending:
                    break
                
                from shared.utils import has_recent_activity
                if has_recent_activity(self.config.project_dir, seconds=60):
                    logger.info("Agent timeout exceeded, but file activity detected. Extending wait by 60s...")
                    timeout = 60.0
                    continue
                else:
                    logger.error(f"Cursor Agent CLI timed out ({self.config.timeout}s) and no recent file activity.")
                    process.kill()
                    raise asyncio.TimeoutError
            
            await process.wait()
            stdout = "".join(stdout_buf).encode()
            stderr = "".join(stderr_buf).encode()

            if process.returncode != 0:
                logger.error(f"Cursor process exited with code {process.returncode}")
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
    header = f"  SESSION {iteration} " + ("(INITIALIZATION)" if is_first else "(CODING)")
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
    prompt: str
) -> tuple[str, str]:
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

        context_block = f"""
CURRENT CONTEXT:
Working Directory: {client.config.project_dir}
{feature_status}
{file_tree}
"""
        # We append a reminder to use the code block format and tool usage
        augmented_prompt = prompt + f"\n{context_block}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search."

        logger.debug(f"Sending Augmented Prompt:\n{augmented_prompt}")
        
        result = await client.run_command(augmented_prompt, client.config.project_dir)
        
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
            # Only log full response in debug
            logger.debug(f"Response:\n{response_text}")
        else:
            logger.warning("No text content found in Cursor response.")
            logger.info(f"Full Cursor response: {json.dumps(result, indent=2)}")
        
        # Execute any blocks found in the response
        if response_text:
            logger.info("Processing response blocks...")
            log, actions = await process_response_blocks(response_text, client.config.project_dir, client.config.bash_timeout)
            if log:
                logger.info("Execution Log updated.")
        
        return "continue", response_text

    except Exception as e:
        logger.exception("Error during agent session")
        return "error", str(e)


async def run_autonomous_agent(config: Config) -> None:
    """
    Run the autonomous agent loop.
    """
    log_startup_config(config, logger)
    
    # Create project directory
    config.project_dir.mkdir(parents=True, exist_ok=True)

    # Initialize Client
    client = CursorClient(config)

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

    while True:
        iteration += 1
        if config.max_iterations and iteration > config.max_iterations:
            logger.info(f"\nReached max iterations ({config.max_iterations})")
            break

        print_session_header(iteration, is_first_run)

        # Choose prompt
        if is_first_run:
            prompt = get_initializer_prompt()
            # Note: We don't flip is_first_run to False until we get a success
        else:
            prompt = get_coding_prompt()

        # Run session
        status, response = await run_agent_session(client, prompt)

        if status == "continue":
            consecutive_errors = 0
            is_first_run = False # Successful run, next run is coding
            
            logger.info(f"Agent will auto-continue in {config.auto_continue_delay}s...")
            log_progress_summary(config.project_dir, config.progress_file_path)
            await asyncio.sleep(config.auto_continue_delay)
            
        elif status == "error":
            consecutive_errors += 1
            logger.error(f"Session encountered an error (Attempt {consecutive_errors}/{config.max_consecutive_errors}).")
            
            if consecutive_errors >= config.max_consecutive_errors:
                logger.critical(f"Too many consecutive errors ({config.max_consecutive_errors}). Stopping execution.")
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
