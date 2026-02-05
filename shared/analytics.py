"""
Analytics Utilities
===================

Functions for gathering and displaying project analytics (Git, Code, etc.).
"""

import shutil
import subprocess
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

def get_git_contributors(project_dir: Path) -> list[tuple[int, str]]:
    """Returns a list of contributors sorted by commit count."""
    git_path = shutil.which("git")
    if not git_path:
        return []

    try:
        # Use shortlog for a nice summary
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "shortlog", "-sn", "--all", "--no-merges"],
            capture_output=True, text=True, check=True
        )
        contributors = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    count, name = parts
                    contributors.append((int(count), name))
        return contributors
    except subprocess.CalledProcessError:
        return []

def get_git_hotspots(project_dir: Path, limit: Optional[int] = 10) -> list[tuple[str, int]]:
    """Returns the most frequently modified files."""
    git_path = shutil.which("git")
    if not git_path:
        return []

    try:
        # Get list of all changed files in all commits
        # Use Popen to stream output instead of loading it all into memory
        process = subprocess.Popen(
            [git_path, "-C", str(project_dir), "log", "--format=format:", "--name-only"],
            stdout=subprocess.PIPE,
            text=True
        )

        counter = Counter()
        if process.stdout:
            for line in process.stdout:
                line = line.strip()
                if line:
                    counter[line] += 1

        process.wait()

        if process.returncode != 0:
            return []

        return counter.most_common(limit)
    except (OSError, subprocess.SubprocessError):
        return []

def get_git_activity(project_dir: Path, days: int = 30) -> list[tuple[str, int]]:
    """Returns commit counts per day for the last N days."""
    git_path = shutil.which("git")
    if not git_path:
        return []

    try:
        # Get dates of all commits
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "log", f"--since={since_date}", "--date=short", "--format=%ad"],
            capture_output=True, text=True, check=True
        )

        dates = [line for line in result.stdout.split('\n') if line]
        counter = Counter(dates)

        # Sort by date
        sorted_activity = sorted(counter.items())
        return sorted_activity
    except subprocess.CalledProcessError:
        return []

def _run_analytics_git_logic(project_dir: Path):
    """Orchestrates the git analytics display."""
    project_dir = project_dir.resolve()
    print(f"--- Git Analytics: {project_dir.name} ---\n")

    if not (project_dir / ".git").is_dir():
        print("❌ Error: Not a git repository.")
        return

    # 1. Contributors
    contributors = get_git_contributors(project_dir)
    print("[ Top Contributors ]")
    if contributors:
        for count, name in contributors[:5]: # Show top 5
            print(f"  {count:<5} {name}")
    else:
        print("  No contributors found.")
    print("")

    # 2. Hotspots
    hotspots = get_git_hotspots(project_dir, limit=5)
    print("[ Hotspots (Most Changed Files) ]")
    if hotspots:
        max_len = max(len(f) for f, _ in hotspots) if hotspots else 10
        for filename, count in hotspots:
            print(f"  {filename:<{max_len}} : {count} commits")
    else:
        print("  No hotspots found.")
    print("")

    # 3. Recent Activity
    activity = get_git_activity(project_dir, days=14)
    print("[ Recent Activity (Last 14 Days) ]")
    if activity:
        # Simple ASCII bar chart
        max_commits = max(count for _, count in activity) if activity else 1
        for date, count in activity:
            bar = "█" * int((count / max_commits) * 20)
            if not bar: bar = "▏" # At least show something for 1 commit if scaling makes it 0
            print(f"  {date} : {count:<3} {bar}")
    else:
        print("  No recent activity.")
    print("")
