"""
Bisect Logic
============

Logic for the 'bisect' command to automate regression finding and analysis.
"""

import asyncio
import logging
import shutil
import subprocess
import re
import shlex
from pathlib import Path
from typing import Optional

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

async def analyze_commit(
    project_dir: Path,
    commit_hash: str,
    bug_description: str,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False,
) -> str:
    """
    Analyzes a specific commit to explain why it might have caused a bug.
    """
    # 1. Get Commit Details (Diff and Message)
    git_path = shutil.which("git")
    if not git_path:
        return "Error: Git not found."

    try:
        # Get commit message and metadata
        show_cmd = [git_path, "-C", str(project_dir), "show", "--stat", commit_hash]
        show_result = subprocess.run(show_cmd, capture_output=True, text=True, check=True)
        commit_info = show_result.stdout

        # Get full diff (limit size if necessary)
        diff_cmd = [git_path, "-C", str(project_dir), "show", commit_hash]
        diff_result = subprocess.run(diff_cmd, capture_output=True, text=True, check=True)
        commit_diff = diff_result.stdout

        # Hard limit to avoid context window explosion (e.g. 50kb)
        if len(commit_diff) > 50000:
            commit_diff = commit_diff[:50000] + "\n... (Diff truncated) ..."

    except subprocess.CalledProcessError as e:
        return f"Error getting commit info: {e}"

    # 2. Setup Agent
    config = Config(
        project_dir=project_dir,
        agent_type=agent_type,
        model=model,
        verbose=verbose,
        max_iterations=1,
        stream_output=False, # We want to capture it
    )

    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }

    agent_class = agent_class_map.get(agent_type)
    if not agent_class:
        return f"Error: Unknown agent type: {agent_type}"

    agent = agent_class(config)

    # 3. Construct Prompt
    prompt = f"""
You are an expert software engineer.
A regression has been identified in the following commit.

BUG/FAILURE DESCRIPTION:
{bug_description}

COMMIT INFO:
{commit_info}

COMMIT DIFF:
{commit_diff}

TASK:
Analyze the changes in this commit and explain EXACTLY why it caused the reported bug/failure.
Be specific about which lines of code are problematic.
If possible, suggest a fix.
"""

    # 4. Run Agent
    logger.info(f"Analyzing commit {commit_hash} with {agent_type}...")
    try:
        status, response, actions = await agent.run_agent_session(prompt)
        return response
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return f"Error during analysis: {e}"


async def run_bisect_logic(
    project_dir: Path,
    good_commit: str,
    bad_commit: str,
    run_command: str,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    verbose: bool = False,
    no_analysis: bool = False,
) -> bool:
    """
    Runs git bisect and optionally analyzes the bad commit.
    """
    git_path = shutil.which("git")
    if not git_path:
        print("❌ Error: 'git' command not found.")
        return False

    print(f"--- Starting Smart Bisect in: {project_dir} ---")
    print(f"  Good: {good_commit}")
    print(f"  Bad:  {bad_commit}")
    print(f"  Command: {run_command}")

    # Ensure clean state or warn?
    # subprocess.run([git_path, "bisect", "reset"], cwd=project_dir) # Just in case

    try:
        # 1. Start Bisect
        subprocess.run(
            [git_path, "bisect", "start", bad_commit, good_commit],
            cwd=project_dir, check=True, capture_output=True # Capture to reduce noise
        )

        # 2. Run Bisect
        print("\nRunning automated bisect (this may take time)...")
        # We want to stream output so user sees progress, but also capture it to find the result
        process = subprocess.Popen(
            [git_path, "bisect", "run"] + shlex.split(run_command),
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        bad_commit_hash = None
        full_output = []

        # Stream output
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(line, end="")
                full_output.append(line)
                # Check for "is the first bad commit"
                # e.g. "b01d... is the first bad commit"
                match = re.search(r"^([a-f0-9]+) is the first (?:'bad'|bad) commit", line)
                if match:
                    bad_commit_hash = match.group(1)

        rc = process.poll()

        # 3. Cleanup
        subprocess.run([git_path, "bisect", "reset"], cwd=project_dir, check=True, capture_output=True)

        if rc != 0:
            print("\n❌ Git bisect run failed (command returned error code).")
            return False

        if bad_commit_hash:
            print(f"\n✅ Bisect Complete! The first bad commit is: {bad_commit_hash}")

            if not no_analysis:
                print("\n--- AI Analysis ---")
                print("Asking agent to analyze the culprit...")
                analysis = await analyze_commit(
                    project_dir,
                    bad_commit_hash,
                    f"The command '{run_command}' failed on this commit.",
                    agent_type,
                    model,
                    verbose
                )
                print("\n" + analysis)
            return True
        else:
            print("\n❌ Could not identify the bad commit. Bisect output unclear.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Error during git bisect: {e}")
        subprocess.run([git_path, "bisect", "reset"], cwd=project_dir, capture_output=True)
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        subprocess.run([git_path, "bisect", "reset"], cwd=project_dir, capture_output=True)
        return False
