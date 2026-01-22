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
from typing import Optional, Any, Dict, List, Tuple

from shared.debt import DebtCollector
from shared.security import SecurityAuditor


def get_git_contributors(project_dir: Path) -> List[Tuple[int, str]]:
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

def get_git_hotspots(project_dir: Path, limit: Optional[int] = 10) -> List[Tuple[str, int]]:
    """Returns the most frequently modified files."""
    git_path = shutil.which("git")
    if not git_path:
        return []

    try:
        # Get list of all changed files in all commits
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "log", "--format=format:", "--name-only"],
            capture_output=True, text=True, check=True
        )

        # Filter out empty lines and count
        files = [line for line in result.stdout.split('\n') if line]
        counter = Counter(files)

        return counter.most_common(limit)
    except subprocess.CalledProcessError:
        return []

def get_git_activity(project_dir: Path, days: int = 30) -> List[Tuple[str, int]]:
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


def collect_analytics_data(project_dir: Path) -> Dict[str, Any]:
    """Collects analytics data for the dashboard."""
    debt_collector = DebtCollector(project_dir)
    security_auditor = SecurityAuditor(project_dir)

    # Debt
    debt_metrics = debt_collector.collect()
    debt_score, debt_grade = debt_collector.calculate_score(debt_metrics)

    # Security
    security_findings = security_auditor.scan_secrets()

    return {
        "debt": {"metrics": debt_metrics, "score": debt_score, "grade": debt_grade},
        "security": security_findings
    }
