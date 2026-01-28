from pathlib import Path
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, Button, DataTable, ListView, ListItem
from textual import on
from shared.cron_lab import CronLabManager

class CronLabTab(Container):
    """Tab for experimenting with cron expressions."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CronLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Cron Lab[/bold]", classes="welcome-text")

            with Horizontal():
                # Left Pane: Input and Presets
                with Vertical(id="cron-input-container", classes="stat-box"):
                    yield Label("Cron Expression:")
                    yield Input(placeholder="* * * * *", id="cron-input")
                    yield Button("Calculate", id="btn-cron-calc", variant="primary")

                    yield Label("[bold]Presets[/bold]")
                    yield ListView(id="cron-presets")

                # Right Pane: Results
                with Vertical(id="cron-results-container", classes="stat-box"):
                    yield Label("[bold]Description[/bold]")
                    yield Label("", id="cron-description")

                    yield Label("[bold]Next 5 Occurrences[/bold]")
                    yield DataTable(id="cron-next-table")

    def on_mount(self) -> None:
        table = self.query_one("#cron-next-table", DataTable)
        table.add_columns("Timestamp", "Relative")

        self.load_presets()

    def load_presets(self) -> None:
        presets = [
            ("* * * * *", "Every Minute"),
            ("*/5 * * * *", "Every 5 Minutes"),
            ("0 * * * *", "Hourly"),
            ("0 0 * * *", "Daily (Midnight)"),
            ("0 0 * * 0", "Weekly (Sunday)"),
            ("0 0 1 * *", "Monthly (1st)"),
        ]

        lv = self.query_one("#cron-presets", ListView)
        for expr, desc in presets:
            # We explicitly set item name to expression for retrieval
            item = ListItem(Label(f"[bold]{desc}[/bold]\n[dim]{expr}[/dim]"))
            item.name = expr
            lv.append(item)

    @on(ListView.Selected, "#cron-presets")
    def on_preset_selected(self, event: ListView.Selected) -> None:
        # In Textual, we can store data on the item or use index.
        # Since I set item.name, I should be able to retrieve it.
        # But wait, ListItem.name is a widget identifier, might conflict if duplicates.
        # Let's use a custom attribute if possible, or just parse the Label.

        # Safer way: retrieve from list of presets by index
        if event.item:
            # Try to get the expression from the label text if stored name fails or is not supported this way
            # But wait, I set item.name = expr.
            if hasattr(event.item, "name") and event.item.name:
                 self.query_one("#cron-input", Input).value = event.item.name
                 self.calculate()

    @on(Button.Pressed, "#btn-cron-calc")
    def on_calc_pressed(self) -> None:
        self.calculate()

    @on(Input.Submitted, "#cron-input")
    def on_input_submitted(self) -> None:
        self.calculate()

    def calculate(self) -> None:
        expr = self.query_one("#cron-input", Input).value
        desc_lbl = self.query_one("#cron-description", Label)
        table = self.query_one("#cron-next-table", DataTable)

        if not expr:
            desc_lbl.update("Please enter an expression.")
            return

        if not self.manager.validate(expr):
            desc_lbl.update("[red]Invalid cron expression.[/red]")
            table.clear()
            return

        # Description
        desc = self.manager.describe(expr)
        desc_lbl.update(f"[green]{desc}[/green]")

        # Next occurrences
        occurrences = self.manager.get_next_occurrences(expr)
        table.clear()
        now = datetime.now()

        for occ_str in occurrences:
            try:
                occ_dt = datetime.fromisoformat(occ_str)
                delta = occ_dt - now

                # Simple relative formatting
                total_seconds = int(delta.total_seconds())
                if total_seconds < 60:
                    relative = f"in {total_seconds}s"
                elif total_seconds < 3600:
                    relative = f"in {total_seconds // 60}m"
                elif total_seconds < 86400:
                    relative = f"in {total_seconds // 3600}h"
                else:
                    relative = f"in {total_seconds // 86400}d"

                table.add_row(occ_str, relative)
            except ValueError:
                table.add_row(occ_str, "-")
