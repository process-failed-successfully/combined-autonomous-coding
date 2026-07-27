from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.objectid_lab import ObjectIdLabManager

class ObjectIdLabTab(Container):
    """Tab for ObjectId operations (Generate, Inspect)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = ObjectIdLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]ObjectId Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Generate Tab
                with TabPane("Generate"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Generate ObjectIds[/bold]")

                        with Horizontal():
                            yield Label("Count:")
                            yield Input(placeholder="1", id="input-objectid-count", type="integer", value="1")

                        yield Button("Generate", id="btn-objectid-generate", variant="primary")

                        yield Label("[bold]Output:[/bold]")
                        yield RichLog(id="log-objectid-generate", wrap=True, highlight=True, markup=True)

                # Inspect Tab
                with TabPane("Inspect"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Inspect ObjectId[/bold]")
                        yield Input(placeholder="Enter ObjectId to inspect", id="input-objectid-inspect")
                        yield Button("Inspect", id="btn-objectid-inspect", variant="primary")

                        yield Label("[bold]Inspection Result:[/bold]")
                        yield RichLog(id="log-objectid-inspect", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-objectid-generate")
    def action_generate(self) -> None:
        count_input = self.query_one("#input-objectid-count", Input).value
        log = self.query_one("#log-objectid-generate", RichLog)

        try:
            count = int(count_input) if count_input else 1
        except ValueError:
            log.write("[bold red]Error: Count must be an integer.[/bold red]")
            return

        try:
            results = self.manager.generate(count=count)
            log.clear()
            for res in results:
                log.write(res)
        except Exception as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-objectid-inspect")
    def action_inspect(self) -> None:
        objectid_input = self.query_one("#input-objectid-inspect", Input).value
        log = self.query_one("#log-objectid-inspect", RichLog)
        log.clear()

        if not objectid_input:
            log.write("[bold red]Please enter an ObjectId to inspect.[/bold red]")
            return

        info = self.manager.inspect(objectid_input.strip())

        if not info.get("valid"):
            log.write(f"[bold red]Error: {info.get('error')}[/bold red]")
            return

        log.write(f"[bold green]Valid ObjectId[/bold green]")
        log.write(f"Generation Time: {info['generation_time']}")
