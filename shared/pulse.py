"""
Pulse Dashboard
===============

Provides a "pulse check" on the project's health by aggregating metrics.
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import math

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import BarColumn, Progress, TextColumn
from rich.text import Text
from rich.columns import Columns
from rich.tree import Tree
from rich import box

from shared.analytics import get_git_activity
from shared.complexity import analyze_project_complexity
from shared.todos import scan_todos
from shared.security import SecurityAuditor

class PulseManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.console = Console()

    def collect_metrics(self) -> Dict[str, Any]:
        """Collects all metrics for the dashboard."""
        metrics = {}

        # 1. Git Activity
        try:
            metrics["activity"] = get_git_activity(self.project_dir, days=14)
        except Exception:
            metrics["activity"] = []

        # 2. Complexity
        try:
            metrics["complexity"] = analyze_project_complexity(self.project_dir)
        except Exception:
            metrics["complexity"] = []

        # 3. TODOs
        try:
            metrics["todos"] = scan_todos(self.project_dir)
        except Exception:
            metrics["todos"] = []

        # 4. Security (Fast Scan)
        try:
            auditor = SecurityAuditor(self.project_dir)
            metrics["security"] = auditor.scan_secrets()
        except Exception:
            metrics["security"] = []

        return metrics

    def calculate_health_score(self, metrics: Dict[str, Any]) -> int:
        """Calculates a health score from 0 to 100."""
        score = 100
        penalties = []

        # Complexity Penalty
        # -5 for each file > 10 avg complexity (capped at 30)
        high_complexity = [f for f in metrics.get("complexity", []) if f.get("complexity", 0) > 10]
        comp_penalty = min(len(high_complexity) * 5, 30)
        score -= comp_penalty
        if comp_penalty > 0:
            penalties.append(f"High Complexity (-{comp_penalty})")

        # TODO Penalty
        # -1 for every 5 TODOs (capped at 20)
        todos_count = len(metrics.get("todos", []))
        todo_penalty = min(math.floor(todos_count / 5), 20)
        score -= todo_penalty
        if todo_penalty > 0:
            penalties.append(f"Too many TODOs (-{todo_penalty})")

        # Security Penalty
        # -10 per HIGH, -5 per MEDIUM (capped at 40)
        sec_penalty = 0
        for issue in metrics.get("security", []):
            sev = str(issue.get("severity", "")).upper()
            if sev == "HIGH":
                sec_penalty += 10
            elif sev == "MEDIUM":
                sec_penalty += 5

        sec_penalty = min(sec_penalty, 40)
        score -= sec_penalty
        if sec_penalty > 0:
            penalties.append(f"Security Issues (-{sec_penalty})")

        # Activity Penalty
        # -10 if inactive for > 7 days
        activity = metrics.get("activity", [])
        is_active = False
        if activity:
            last_date_str = activity[-1][0] # date is first element
            try:
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                if (datetime.now() - last_date).days <= 7:
                    is_active = True
            except ValueError:
                pass

        if not is_active and not activity: # Treat no history as inactive too
             score -= 10
             penalties.append("Inactive Project (-10)")
        elif not is_active:
             score -= 10
             penalties.append("Inactive > 7 days (-10)")

        return max(0, score)

    def render_dashboard(self, metrics: Dict[str, Any], score: int):
        """Renders the dashboard using Rich."""

        # --- Header ---
        score_color = "green"
        if score < 50:
            score_color = "red"
        elif score < 80:
            score_color = "yellow"

        header_text = Text(f"Project Pulse: {self.project_dir.name}", style="bold white")
        score_text = Text(f"Health Score: {score}/100", style=f"bold {score_color}")

        header = Panel(
            Columns([header_text, score_text], expand=True),
            style="blue",
            box=box.ROUNDED
        )

        # --- Activity (Sparkline-ish) ---
        activity = metrics.get("activity", [])
        if activity:
            # Normalize for bar height (1-8 blocks)
            counts = [count for _, count in activity]
            max_count = max(counts) if counts else 1
            bars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

            chart = ""
            for count in counts:
                idx = int((count / max_count) * 7)
                chart += bars[idx]

            activity_panel = Panel(
                Text(chart, style="cyan"),
                title=f"Activity (Last {len(activity)} days)",
                border_style="cyan",
                box=box.ROUNDED
            )
        else:
            activity_panel = Panel("No recent activity", title="Activity", border_style="dim")


        # --- Hotspots (Complexity) ---
        complex_files = sorted(metrics.get("complexity", []), key=lambda x: x["complexity"], reverse=True)[:5]

        hotspot_table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
        hotspot_table.add_column("File")
        hotspot_table.add_column("Complexity", justify="right")

        if complex_files:
            for f in complex_files:
                c_val = f["complexity"]
                color = "red" if c_val > 10 else "green"
                hotspot_table.add_row(
                    f["file"] + f":{f['function']}",
                    Text(str(c_val), style=color)
                )
        else:
            hotspot_table.add_row("No complexity data", "")

        hotspot_panel = Panel(
            hotspot_table,
            title="Complexity Hotspots",
            border_style="magenta",
            box=box.ROUNDED
        )

        # --- Issues Summary ---
        todos = metrics.get("todos", [])
        security = metrics.get("security", [])

        issues_table = Table(box=box.SIMPLE, show_header=False)
        issues_table.add_row("TODOs", str(len(todos)))
        issues_table.add_row("Security Findings", str(len(security)))

        issues_panel = Panel(
            issues_table,
            title="Issues Summary",
            border_style="yellow",
            box=box.ROUNDED
        )

        # --- Layout ---
        # Top: Header
        # Middle: Activity
        # Bottom: Split Hotspots / Issues

        self.console.print(header)
        self.console.print(activity_panel)

        bottom_columns = Columns([hotspot_panel, issues_panel], expand=True)
        self.console.print(bottom_columns)

        # --- Next Steps / Suggestions ---
        suggestions = []
        if score < 100:
            if any(f["complexity"] > 10 for f in complex_files):
                suggestions.append("- Refactor high complexity functions shown above.")
            if len(todos) > 20:
                suggestions.append("- Address pending TODOs.")
            if security:
                suggestions.append("- Fix security vulnerabilities (run 'main.py security').")
            if not activity:
                 suggestions.append("- Commit recent changes.")

        if suggestions:
            suggestion_panel = Panel(
                "\n".join(suggestions),
                title="Recommended Actions",
                border_style="green",
                box=box.ROUNDED
            )
            self.console.print(suggestion_panel)

def run_pulse_logic(project_dir: Path):
    manager = PulseManager(project_dir)
    with Console().status("[bold green]Checking pulse..."):
        metrics = manager.collect_metrics()
        score = manager.calculate_health_score(metrics)

    manager.render_dashboard(metrics, score)
