from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, Button, DataTable
from textual import on
from shared.logic_lab import LogicLabManager
import asyncio

class LogicLabTab(Container):
    """Tab for Truth Table Logic Lab."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = LogicLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Logic Lab (Truth Table Generator)[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Expression:", classes="label")
                yield Input(placeholder="e.g. A and (B or !C)", id="logic-input")
                yield Button("Generate Table", id="btn-logic-generate", variant="primary")

            yield Label("", id="logic-status")
            yield DataTable(id="logic-table")

    def on_mount(self) -> None:
        table = self.query_one("#logic-table", DataTable)
        table.cursor_type = "row"

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-logic-generate":
            await self.generate_table()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "logic-input":
            await self.generate_table()

    async def generate_table(self) -> None:
        expr = self.query_one("#logic-input", Input).value
        status = self.query_one("#logic-status", Label)
        table = self.query_one("#logic-table", DataTable)

        table.clear(columns=True)

        if not expr:
            status.update("[red]Please enter an expression.[/red]")
            return

        status.update("Generating...")

        # Run in thread
        data = await asyncio.to_thread(self.manager.generate_truth_table, expr)

        if data.get("error"):
            status.update(f"[red]Error: {data['error']}[/red]")
            return

        status.update("[green]Table generated.[/green]")

        # Columns: Variables... | Result
        variables = data["variables"]
        cols = variables + ["Result"]
        table.add_columns(*cols)

        # Rows
        for row in data["rows"]:
            cells = []
            # Add variable values
            for var in variables:
                val = row["values"][var]
                display = "[green]T[/green]" if val else "[dim]F[/dim]"
                cells.append(display)

            # Result
            res = row["result"]
            res_display = "[bold green]TRUE[/bold green]" if res else "[bold red]FALSE[/bold red]"
            cells.append(res_display)

            table.add_row(*cells)
