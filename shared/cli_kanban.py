from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from shared.task_manager import TaskManager, Task

COLUMNS_MAP = {
    "todo": ["pending", "open", "to do", "todo", "new", "reopened"],
    "in_progress": ["in_progress", "in progress", "active", "developing", "review", "test", "in review"],
    "done": ["completed", "done", "closed", "fixed", "resolved", "merged"]
}

def get_column_id(status: str) -> str:
    status = str(status).lower().replace("-", "_")
    if status in COLUMNS_MAP["done"]:
        return "done"
    elif status in COLUMNS_MAP["in_progress"]:
        return "in_progress"
    return "todo"

def run_kanban_logic(project_dir, action="view", task_id=None, status=None):
    manager = TaskManager(project_dir)
    console = Console()

    if action == "move":
        if not task_id or not status:
            console.print("[bold red]Error:[/bold red] --task-id and --status are required for 'move'.")
            return False

        console.print(f"Moving task [bold]{task_id}[/bold] to [bold]{status}[/bold]...")
        if manager.update_task_status(task_id, status):
            console.print(f"[bold green]Success![/bold green] Updated {task_id}.")
            return True
        else:
            console.print(f"[bold red]Failed.[/bold red] Could not update {task_id}. (Note: GitHub and TODOs are currently read-only)")
            return False

    # Default: view
    tasks = manager.fetch_all_tasks()

    # Organize tasks into columns
    columns = {"todo": [], "in_progress": [], "done": []}

    for task in tasks:
        col_id = get_column_id(task.status)
        columns[col_id].append(task)

    # Render Table
    table = Table(title=f"Kanban Board: {project_dir.name}", box=box.ROUNDED, expand=True)
    table.add_column("To Do", style="red")
    table.add_column("In Progress", style="yellow")
    table.add_column("Done", style="green")

    # Determine max rows
    max_rows = max(len(columns["todo"]), len(columns["in_progress"]), len(columns["done"]))

    for i in range(max_rows):
        row_cells = []
        for col_name in ["todo", "in_progress", "done"]:
            if i < len(columns[col_name]):
                task = columns[col_name][i]

                # Format card content
                source_tag = f"[{task.source.upper()}]"
                priority_icon = "🔴" if task.priority == "High" else "🟢" if task.priority == "Low" else "⚪"

                content = f"{priority_icon} [bold]{task.id}[/bold]\n{task.title}"
                if task.metadata.get("assignee"):
                    content += f"\n[dim]@{task.metadata['assignee']}[/dim]"

                # Wrap in Panel for card look
                card = Panel(content, border_style="dim", expand=True)
                row_cells.append(card)
            else:
                row_cells.append("")

        table.add_row(*row_cells)

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
    else:
        console.print(table)
        console.print("\n[dim]Tip: Move tasks with 'kanban move <ID> <STATUS>'[/dim]")

    return True
