"""
Standup Generator
=================

Generates a daily standup report based on git activity.
"""

import logging
import shutil
import subprocess
import io
import contextlib
from pathlib import Path
from typing import Optional, List, Dict, Any

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)


def get_commits_since(project_dir: Path, since: str, author: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Fetches commits since a specific time.

    Args:
        project_dir: Path to the project root.
        since: Time string (e.g., "24 hours ago", "yesterday").
        author: Optional author name/email filter.

    Returns:
        List of dictionaries with commit details.
    """
    git_path = shutil.which("git")
    if not git_path:
        return []

    cmd = [
        git_path,
        "-C", str(project_dir),
        "log",
        f"--since={since}",
        "--pretty=format:%h|%an|%ad|%s%n%b%n---COMMIT_END---",
        "--date=local"  # Use local time for standup relevance
    ]

    if author:
        cmd.append(f"--author={author}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        commits = []
        raw_entries = result.stdout.split("---COMMIT_END---\n")

        for entry in raw_entries:
            entry = entry.strip()
            if not entry:
                continue

            # First line is metadata, rest is body
            lines = entry.split('\n', 1)
            meta = lines[0].split('|', 3)

            if len(meta) < 4:
                continue

            commit_hash = meta[0]
            commit_author = meta[1]
            date = meta[2]
            subject = meta[3]
            body = lines[1].strip() if len(lines) > 1 else ""

            commits.append({
                "hash": commit_hash,
                "author": commit_author,
                "date": date,
                "subject": subject,
                "body": body
            })

        return commits

    except subprocess.CalledProcessError as e:
        logger.error(f"Error fetching commits: {e}")
        return []


async def generate_standup_report(
    commits: List[Dict[str, str]],
    agent_type: str,
    model: Optional[str] = None,
    project_dir: Optional[Path] = None,
    since: str = "24 hours ago"
) -> str:
    """
    Generates a standup report using AI based on the provided commits.
    """
    if not commits:
        return "No commits found."

    # Prepare Prompt
    commits_text = ""
    for c in commits:
        commits_text += f"- {c['date']} [{c['hash'][:7]}] {c['subject']}\n"
        if c['body']:
            commits_text += f"  Details: {c['body']}\n"

    prompt = f"""
    You are an AI assistant helping a developer write a daily standup report.

    Based on the following git commit history from the last {since}, generate a concise standup update.

    Format the output as follows:

    **Yesterday/Today I worked on:**
    - [List key achievements/changes]

    **Technical Context:**
    - [Briefly mention technical details or refactors if any]

    **Plan/Next Steps:**
    - [Infer logical next steps based on the work done (e.g. if a test was fixed, maybe next is a feature. If a feature was started, finish it.)]

    --- Git History ---
    {commits_text}
    """

    # Initialize Agent
    # If project_dir is None, use current dir, though Config usually requires it.
    p_dir = project_dir or Path(".")

    config = Config(
        project_dir=p_dir,
        agent_type=agent_type,
        model=model,
        verbose=False,
        max_iterations=1,
        stream_output=True
    )

    agent_class_map = {
        "gemini": GeminiAgent,
        "cursor": CursorAgent,
        "local": LocalAgent,
        "openrouter": OpenRouterAgent,
    }

    agent_class: Any = agent_class_map.get(config.agent_type, GeminiAgent)
    agent = agent_class(config)

    # Capture output if streaming is enabled by agent, but we want to return the string.
    # Most agents print to stdout if stream_output is True.
    # We'll use io.StringIO to capture it.

    output_capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_capture):
            await agent.run_agent_session(prompt)
        return output_capture.getvalue()
    except Exception as e:
        logger.error(f"Error generating standup: {e}")
        return f"Error generating report: {e}"


async def run_standup_logic(args) -> bool:
    """
    Executes the standup generation logic (CLI entry point).
    """
    project_dir = args.project_dir.resolve()
    since = args.since
    author = args.author

    # If author is not specified, try to detect current user
    if not author:
        try:
            res = subprocess.run(
                ["git", "config", "user.name"],
                cwd=project_dir, capture_output=True, text=True
            )
            author = res.stdout.strip()
        except Exception:
            pass

    print("--- Generating Standup Report ---")
    print(f"Project: {project_dir}")
    print(f"Since: {since}")
    print(f"Author: {author or 'All'}")

    commits = get_commits_since(project_dir, since, author)

    if not commits:
        print("❌ No commits found matching criteria.")
        return True

    print(f"Found {len(commits)} commit(s).")
    print("\n--- Standup Report ---\n")

    report = await generate_standup_report(
        commits=commits,
        agent_type=args.agent or "gemini",
        model=args.model,
        project_dir=project_dir,
        since=since
    )

    print(report)
    return True
