"""
Debug Logic
===========

Executes a shell command and uses AI to analyze failures.
"""

import sys
import asyncio
import shlex
from pathlib import Path
from agents.shared.prompts import get_debug_prompt
from shared.agent_client import AgentClient


async def _stream_output(stream, output_list, destination):
    """Reads from a stream line by line, printing to destination and appending to output_list."""
    while True:
        line = await stream.readline()
        if not line:
            break
        # Decode with replacement to handle binary output safely
        decoded_line = line.decode('utf-8', errors='replace')
        print(decoded_line, end="", file=destination)
        output_list.append(decoded_line)


async def run_debug_logic(
    command_list: list[str],
    project_dir: Path,
    agent_type: str = "gemini",
    model: str = None,
    verbose: bool = False
) -> bool:
    """
    Executes a command. If it fails, asks the AI to explain and fix it.
    Uses asyncio to avoid blocking and deadlocks.
    """
    # Use shlex.join for proper command escaping
    command_str = shlex.join(command_list)
    print(f"--- Debugging Command: {command_str} ---")
    print(f"  Working Directory: {project_dir}")

    try:
        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            *command_list,
            cwd=project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_output = []
        stderr_output = []

        # Gather output concurrently to prevent deadlock
        await asyncio.gather(
            _stream_output(process.stdout, stdout_output, sys.stdout),
            _stream_output(process.stderr, stderr_output, sys.stderr)
        )

        # Wait for the process to exit
        return_code = await process.wait()

        if return_code == 0:
            print("\n✅ Command executed successfully.")
            return True

        print(f"\n❌ Command failed with exit code {return_code}.")
        print("🤖 Asking agent for diagnosis...")

        stdout_str = "".join(stdout_output)
        stderr_str = "".join(stderr_output)

        # Initialize Agent
        client = AgentClient(agent_id="debugger")

        # Prepare Prompt
        prompt_template = get_debug_prompt()
        prompt = prompt_template.format(
            command=command_str,
            project_dir=project_dir,
            stdout=stdout_str,
            stderr=stderr_str
        )

        # Call Agent
        response = await client.ask_agent(
            prompt=prompt,
            agent_type=agent_type,
            model=model,
            project_dir=project_dir
        )

        print("\n--- Agent Diagnosis & Fix ---")
        print(response)
        print("-----------------------------")

        return False

    except FileNotFoundError:
        print(f"❌ Error: Command '{command_list[0]}' not found.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        return False
