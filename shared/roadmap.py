from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import BarColumn, TextColumn, Progress
from rich.style import Style
from shared.feature_list import load_feature_list

def run_roadmap_logic(project_dir: Path):
    """
    Displays a roadmap/progress view of the features in feature_list.json.
    """
    console = Console()
    feature_file = project_dir / "feature_list.json"

    if not feature_file.exists():
        console.print("[red]❌ No feature_list.json found.[/red]")
        return False

    features = load_feature_list(feature_file)
    if not features:
        console.print("[yellow]⚠️  feature_list.json is empty.[/yellow]")
        return True

    # Statistics
    total = len(features)
    completed = 0
    failed = 0
    in_progress = 0

    processed_features = []

    for f in features:
        status_str = f.get("status", "").lower()
        passes = f.get("passes")

        display_status = "PENDING"
        style = "dim"
        icon = "○"

        if passes is True or status_str == "completed":
            display_status = "COMPLETED"
            style = "green"
            icon = "✅"
            completed += 1
        elif passes is False or status_str == "failed":
            display_status = "FAILED"
            style = "red"
            icon = "❌"
            failed += 1
        elif status_str == "in_progress":
            display_status = "IN PROGRESS"
            style = "yellow"
            icon = "🚧"
            in_progress += 1
        else:
            # Pending
            pass

        processed_features.append({
            "title": f.get("title", "No Title"),
            "description": f.get("description", ""),
            "status": display_status,
            "style": style,
            "icon": icon,
            "id": f.get("id", "")
        })

    # Progress Bar
    console.print(f"\n[bold]🚀 Project Roadmap: {project_dir.name}[/bold]\n")

    # Calculate percentage
    percent = (completed / total) * 100 if total > 0 else 0

    # Custom progress bar using rich
    # We use a simple Bar chart or just text representation since Progress is for live updates usually

    bar_width = 40
    filled_width = int(bar_width * (percent / 100))
    bar = f"[{'#' * filled_width}{'-' * (bar_width - filled_width)}]"

    color = "green" if percent == 100 else "cyan"
    console.print(f"[{color}]{bar} {percent:.1f}%[/] ({completed}/{total} Features)")
    console.print(f"Stats: [green]{completed} Done[/], [yellow]{in_progress} In Progress[/], [red]{failed} Failed[/], [dim]{total - completed - in_progress - failed} Pending[/]\n")

    # Table
    table = Table(show_header=True, header_style="bold magenta", box=None, expand=True)
    table.add_column("Status", width=12, justify="center")
    table.add_column("Feature", style="bold")
    table.add_column("Description", style="dim")

    for pf in processed_features:
        table.add_row(
            f"[{pf['style']}]{pf['icon']} {pf['status']}[/]",
            pf['title'],
            pf['description']
        )

    console.print(table)
    console.print()
    return True
