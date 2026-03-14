"""
CLI Command Generation Logic
============================

Logic for the 'do' command to translate natural language into shell commands.
"""

import logging
import platform
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from agents.shared.prompts import get_cli_prompt
from shared.work_session import WorkSessionManager

logger = logging.getLogger(__name__)


async def run_do_logic(
    instruction: str,
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False,
    yes: bool = False,
    retry: bool = False,
    max_retries: int = 3,
) -> bool:
    """
    Executes the 'do' logic.

    Args:
        instruction: The user's natural language instruction.
        project_dir: The project root directory.
        agent_type: The type of agent to use.
        model: The model to use.
        verbose: Enable verbose logging.
        yes: If True, execute without confirmation.
        retry: If True, retry on failure by asking the agent to correct it.
        max_retries: The maximum number of retries.

    Returns:
        True if successful, False otherwise.
    """

    # Setup Config
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        verbose=verbose,
        max_iterations=1,  # Single shot
        stream_output=False,  # We want just the command first
    )

    # Initialize Agent
    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }

    agent_class = agent_class_map.get(agent_type)
    if not agent_class:
        logger.error(f"Unknown agent type: {agent_type}")
        return False

    agent = agent_class(config)

    # Gather System Context
    cwd = os.getcwd()
    os_name = platform.system()
    shell_name = os.environ.get("SHELL", "unknown")
    if os_name == "Windows":
        shell_name = os.environ.get("COMSPEC", "cmd.exe")

    # Check for active session context
    session_manager = WorkSessionManager(project_dir)
    active_session = session_manager.get_active_session()
    session_context = ""
    if active_session:
        session_context = f"Active Session: {active_session.name}\n"
        if active_session.files:
            session_context += f"Relevant Files: {', '.join(active_session.files)}\n"
        if active_session.notes:
            session_context += f"Session Notes: {'; '.join(active_session.notes)}\n"

        # Append session context to instruction
        instruction = f"{instruction}\n\nContext:\n{session_context}"

    # Construct Prompt
    base_prompt = get_cli_prompt()
    formatted_prompt = base_prompt.format(
        instruction=instruction,
        cwd=cwd,
        os_name=os_name,
        shell_name=shell_name
    )

    logger.info(f"Asking {agent_type} agent to translate: {instruction}")

    current_prompt = formatted_prompt
    attempts = 0
    max_attempts = max_retries + 1 if retry else 1

    while attempts < max_attempts:
        try:
            # We reuse run_agent_session but we expect it might try to execute actions
            # if the prompt wasn't strict enough. The prompt says "No Execution" (implicitly via "Return ONLY...").
            # Note: run_agent_session returns (status, response, actions)
            status, response, actions = await agent.run_agent_session(current_prompt)

            # Clean the response (sometimes models wrap in ```bash ... ```)
            command = response.strip()
            if command.startswith("```"):
                lines = command.splitlines()
                if len(lines) >= 3:
                    # Remove first and last line
                    command = "\n".join(lines[1:-1])

            # Remove language identifier if present (e.g. "bash")
            if command.startswith("bash") or command.startswith("sh"):
                # This is risky if the command actually starts with bash, but usually it's the markdown block info
                # Better: check if it was inside a block
                pass

            command = command.strip()

            if command.startswith("ERROR:"):
                print(f"\n❌ Agent Error: {command[6:].strip()}")
                return False

            if attempts == 0:
                print("\n--- Suggested Command ---")
            else:
                print(f"\n--- Suggested Command (Retry {attempts}/{max_retries}) ---")

            print(f"\033[1m{command}\033[0m")  # Bold
            print("-------------------------")

            if yes:
                should_run = True
            else:
                should_run = False
                while True:
                    confirm = input("Run this command? [y/N/e(xplain)]: ").strip().lower()
                    if confirm == 'y':
                        should_run = True
                        break
                    elif confirm in ['n', '']:
                        should_run = False
                        break
                    elif confirm.startswith('e'):
                        print("\n--- Generating Explanation ---")
                        explain_prompt = f"Explain the following shell command concisely:\n\n`{command}`\n\nProvide ONLY the explanation."
                        try:
                            _, explanation, _ = await agent.run_agent_session(explain_prompt)
                            print(f"{explanation.strip()}\n------------------------------\n")
                        except Exception as e:
                            print(f"❌ Failed to get explanation: {e}\n------------------------------\n")
                    else:
                        print("Invalid option.")

            if should_run:
                print(f"\nRunning: {command}")
                try:
                    # Use shell=True to allow pipes, etc.
                    # B602: subprocess_popen_with_shell_equals_true - Valid here as we are building a shell tool
                    result = subprocess.run(command, shell=True, cwd=cwd, text=True, capture_output=True)  # nosec B602

                    if result.stdout:
                        sys.stdout.write(result.stdout)
                    if result.stderr:
                        sys.stderr.write(result.stderr)

                    if result.returncode == 0:
                        print("✅ Command executed successfully.")
                        return True
                    else:
                        print(f"❌ Command failed with exit code {result.returncode}.")
                        if retry and attempts < max_retries:
                            print("Requesting agent to correct the command...")
                            current_prompt = f"""The previous command failed.
Original Instruction: {instruction}
Failed Command: {command}
Exit Code: {result.returncode}
Standard Output:
{result.stdout}
Standard Error:
{result.stderr}

Please provide a corrected command that fixes the issue. Return ONLY the shell command."""
                        else:
                            return False
                except Exception as e:
                    print(f"❌ Error executing command: {e}")
                    return False
            else:
                print("Aborted.")
                return True

        except Exception as e:
            logger.error(f"Error during 'do' session: {e}")
            return False

        attempts += 1

    return False
