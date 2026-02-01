from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text
from shared.task_manager import TaskManager, Task

def run_kanban_logic(project_dir: Path, action: str = "view", task_id: str = None, status: str = None) -> bool:
    """
    Runs the Kanban CLI logic.
    """
    manager = TaskManager(project_dir)
    console = Console()

    if action == "view":
        tasks = manager.fetch_all_tasks()

        # Categorize tasks
        todo_tasks = []
        in_progress_tasks = []
        done_tasks = []

        # Simple mapping, similar to TUI
        todo_statuses = ["pending", "open", "to do", "todo", "new"]
        in_progress_statuses = ["in_progress", "in progress", "active", "developing"]
        done_statuses = ["completed", "done", "closed", "fixed", "resolved"]

        for task in tasks:
            s = str(task.status).lower().replace("-", "_")
            if s in done_statuses:
                done_tasks.append(task)
            elif s in in_progress_statuses:
                in_progress_tasks.append(task)
            else:
                todo_tasks.append(task)

        # Helper to create a panel for a task
        def create_task_panel(t: Task):
            priority_color = "white"
            if t.priority.lower() == "high":
                priority_color = "red"
            elif t.priority.lower() == "medium":
                priority_color = "yellow"
            elif t.priority.lower() == "low":
                priority_color = "green"

            content = f"[bold]{t.title}[/bold]\n"
            content += f"[{priority_color}]Priority: {t.priority}[/{priority_color}]\n"
            content += f"[dim]{t.source.upper()} {t.id}[/dim]"

            return Panel(content, expand=True)

        # Create columns
        todo_col = [create_task_panel(t) for t in todo_tasks]
        prog_col = [create_task_panel(t) for t in in_progress_tasks]
        done_col = [create_task_panel(t) for t in done_tasks]

        # Use a table to layout the columns
        table = Table(title=f"Kanban Board - {project_dir.name}", show_header=True, expand=True)
        table.add_column("To Do", style="cyan", ratio=1)
        table.add_column("In Progress", style="magenta", ratio=1)
        table.add_column("Done", style="green", ratio=1)

        # Determine max rows
        max_rows = max(len(todo_col), len(prog_col), len(done_col))

        for i in range(max_rows):
            c1 = todo_col[i] if i < len(todo_col) else ""
            c2 = prog_col[i] if i < len(prog_col) else ""
            c3 = done_col[i] if i < len(done_col) else ""
            table.add_row(c1, c2, c3)

        console.print(table)
        return True

    elif action == "move":
        if not task_id or not status:
            console.print("[red]Error: task_id and status are required for 'move' action.[/red]")
            return False

        console.print(f"Moving task [bold]{task_id}[/bold] to [bold]{status}[/bold]...")
        success = manager.update_task_status(task_id, status)

        if success:
            console.print("[green]✅ Task updated successfully.[/green]")
            return True
        else:
            console.print(f"[red]❌ Failed to update task {task_id}.[/red]")
            console.print("Note: Only Sprint and Jira tasks are currently mutable.")
            return False

    return False
