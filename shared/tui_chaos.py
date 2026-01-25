from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, RichLog, Checkbox
from textual.containers import Container, Horizontal, Vertical
from textual import on
from pathlib import Path
import asyncio
from shared.chaos import ChaosManager

class ChaosTab(Container):
    """Tab for running Chaos Engineering experiments."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        # We use a default manager for listing, but instantiate a new one for running to inject printer
        self.manager = ChaosManager(project_dir)
        self.selected_experiment = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Chaos Engineering[/bold]", classes="welcome-text")

            with Horizontal():
                # Left Pane: Experiment List
                with Vertical(id="chaos-list-container", classes="stat-box"):
                    yield Label("[bold]Experiments[/bold]")
                    yield DataTable(id="chaos-table")
                    yield Button("Refresh", id="btn-chaos-refresh", variant="default")

                # Right Pane: Controls and Log
                with Vertical(id="chaos-control-container"):
                    yield Label("[bold]Experiment Details[/bold]")
                    with Horizontal(classes="stat-box"):
                        yield Label("Controls:", classes="label")
                        yield Checkbox("Dry Run", id="chk-chaos-dry", value=True)
                        yield Button("Run Experiment", id="btn-chaos-run", variant="error", disabled=True)

                    yield Label("[bold]Execution Log[/bold]")
                    yield RichLog(id="chaos-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#chaos-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Description")
        self.load_experiments()

    def load_experiments(self) -> None:
        table = self.query_one("#chaos-table", DataTable)
        table.clear()

        for name, cls in self.manager.experiments.items():
            # Instantiate to get description
            exp = cls(self.project_dir)
            table.add_row(name, exp.description, key=name)

    @on(DataTable.RowSelected, "#chaos-table")
    def on_experiment_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_experiment = event.row_key.value
        self.query_one("#btn-chaos-run").disabled = False

        log = self.query_one("#chaos-log", RichLog)
        log.write(f"Selected: [bold]{self.selected_experiment}[/bold]")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-chaos-refresh":
            self.load_experiments()
            self.notify("Experiments refreshed.")
        elif event.button.id == "btn-chaos-run":
            await self.run_experiment()

    async def run_experiment(self) -> None:
        if not self.selected_experiment:
            return

        dry_run = self.query_one("#chk-chaos-dry", Checkbox).value
        log = self.query_one("#chaos-log", RichLog)

        mode = "DRY RUN" if dry_run else "LIVE"
        color = "yellow" if dry_run else "red"

        log.write(f"\n[bold {color}]Running {self.selected_experiment} ({mode})...[/bold {color}]")
        self.notify(f"Running {self.selected_experiment}...", severity="warning" if not dry_run else "information")

        # Thread-safe printer callback
        def tui_printer(message: str):
            # Schedule the write on the main thread
            self.call_from_thread(log.write, message)

        # Create manager instance with custom printer for this run
        manager = ChaosManager(self.project_dir, printer=tui_printer)

        def do_run():
            # We pass yes=True to skip interactive confirmation since we have TUI controls
            return manager.run(self.selected_experiment, dry_run=dry_run, yes=True)

        try:
            success = await asyncio.to_thread(do_run)

            if success:
                log.write(f"[bold green]Experiment {self.selected_experiment} completed successfully.[/bold green]")
                self.notify("Experiment completed.")
            else:
                log.write(f"[bold red]Experiment {self.selected_experiment} failed.[/bold red]")
                self.notify("Experiment failed.", severity="error")

        except Exception as e:
            log.write(f"[bold red]Error running experiment: {e}[/bold red]")
            self.notify(f"Error: {e}", severity="error")
