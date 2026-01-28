from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, Button, RichLog, DataTable
from textual import on
from pathlib import Path
import yaml
from datetime import datetime
from shared.cron_lab import CronLabManager

class CronLabTab(Container):
    """Tab for experimenting with Cron expressions."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CronLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Cron Laboratory[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Expression:", classes="label")
                yield Input(placeholder="* * * * *", id="cron-input")
                yield Button("Validate", id="btn-cron-validate", variant="primary")

            with Vertical(classes="stat-box"):
                yield Label("Status: ", id="lbl-cron-status")
                yield Label("Description: ", id="lbl-cron-desc")

            with Vertical(classes="stat-box"):
                yield Label("[bold]Next Occurrences[/bold]")
                yield DataTable(id="cron-table")

            with Horizontal(classes="stat-box"):
                yield Input(placeholder="Task Name...", id="cron-task-name")
                yield Input(placeholder="Command...", id="cron-task-cmd")
                yield Button("Add to Scheduler", id="btn-cron-add", variant="success", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#cron-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Time", "Relative")

    @on(Input.Changed, "#cron-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        self.validate_expression(event.value)

    @on(Button.Pressed, "#btn-cron-validate")
    def on_validate(self) -> None:
        expr = self.query_one("#cron-input", Input).value
        self.validate_expression(expr)

    def validate_expression(self, expr: str) -> None:
        status_lbl = self.query_one("#lbl-cron-status", Label)
        desc_lbl = self.query_one("#lbl-cron-desc", Label)
        add_btn = self.query_one("#btn-cron-add", Button)
        table = self.query_one("#cron-table", DataTable)

        table.clear()

        if not expr:
            status_lbl.update("Status: Empty")
            desc_lbl.update("Description: ")
            add_btn.disabled = True
            return

        if self.manager.validate(expr):
            status_lbl.update("Status: [green]Valid[/green]")
            desc_lbl.update(f"Description: {self.manager.describe(expr)}")
            add_btn.disabled = False

            # Show next occurrences
            occurrences = self.manager.get_next_occurrences(expr, 5)
            now = datetime.now()
            for dt in occurrences:
                delta = dt - now
                # Format relative time roughly
                if delta.total_seconds() < 60:
                    rel = f"in {int(delta.total_seconds())}s"
                elif delta.total_seconds() < 3600:
                    rel = f"in {int(delta.total_seconds()//60)}m"
                elif delta.total_seconds() < 86400:
                    rel = f"in {int(delta.total_seconds()//3600)}h"
                else:
                    rel = f"in {int(delta.days)}d"

                table.add_row(str(dt), rel)

        else:
            status_lbl.update("Status: [red]Invalid[/red]")
            desc_lbl.update("Description: ")
            add_btn.disabled = True

    @on(Button.Pressed, "#btn-cron-add")
    def on_add(self) -> None:
        expr = self.query_one("#cron-input", Input).value
        name = self.query_one("#cron-task-name", Input).value
        cmd = self.query_one("#cron-task-cmd", Input).value

        if not name or not cmd:
            self.notify("Name and Command required.", severity="error")
            return

        config_path = self.project_dir / "scheduler.yaml"

        # Load existing or create new
        data = {"tasks": []}
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = yaml.safe_load(f) or {"tasks": []}
            except Exception as e:
                self.notify(f"Error reading config: {e}", severity="error")
                return

        # Add task
        new_task = {
            "name": name,
            "command": cmd,
            "cron": expr
        }

        if "tasks" not in data:
            data["tasks"] = []

        data["tasks"].append(new_task)

        try:
            with open(config_path, "w") as f:
                yaml.dump(data, f, sort_keys=False, indent=2)
            self.notify(f"Task '{name}' added to scheduler.")

            # Clear inputs
            self.query_one("#cron-task-name", Input).value = ""
            self.query_one("#cron-task-cmd", Input).value = ""

        except Exception as e:
            self.notify(f"Error saving task: {e}", severity="error")
