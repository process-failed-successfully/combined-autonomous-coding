from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, TabbedContent, TabPane, Static
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.ulid_lab import UlidLabManager


class UlidLabTab(Container):
    """Tab for ULID operations (Generate, Inspect, Validate)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = UlidLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]ULID Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Generate Tab
                with TabPane("Generate"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Generate ULIDs[/bold]")

                        with Horizontal():
                            yield Label("Count:")
                            yield Input(placeholder="1", id="input-ulid-count", type="integer", value="1")

                        yield Button("Generate", id="btn-ulid-generate", variant="primary")

                        yield Label("[bold]Output:[/bold]")
                        yield RichLog(id="log-ulid-generate", wrap=True, highlight=True, markup=True)

                # Inspect Tab
                with TabPane("Inspect"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Inspect ULID[/bold]")
                        with Horizontal():
                            yield Input(placeholder="Enter ULID...", id="input-ulid-inspect")
                            yield Button("Inspect", id="btn-ulid-inspect", variant="warning")

                        yield Label("[bold]Details:[/bold]")
                        yield RichLog(id="log-ulid-inspect", wrap=True, highlight=True, markup=True)

                # Validate Tab
                with TabPane("Validate"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Validate ULID[/bold]")
                        with Horizontal():
                            yield Input(placeholder="Enter ULID...", id="input-ulid-validate")
                            yield Button("Validate", id="btn-ulid-validate", variant="success")

                        yield Static(id="lbl-ulid-validate-result", classes="result-box")

    @on(Button.Pressed, "#btn-ulid-generate")
    def on_generate(self) -> None:
        count_val = self.query_one("#input-ulid-count", Input).value
        count = int(count_val) if count_val.isdigit() else 1

        log = self.query_one("#log-ulid-generate", RichLog)
        log.clear()

        try:
            results = self.manager.generate(count=count)
            for u in results:
                log.write(f"[green]{u}[/green]")
            self.notify(f"Generated {len(results)} ULIDs.")
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify("Generation failed.", severity="error")

    @on(Button.Pressed, "#btn-ulid-inspect")
    def on_inspect(self) -> None:
        val = self.query_one("#input-ulid-inspect", Input).value.strip()
        log = self.query_one("#log-ulid-inspect", RichLog)
        log.clear()

        if not val:
            self.notify("Please enter a ULID.", severity="warning")
            return

        info = self.manager.inspect(val)
        if not info["valid"]:
            log.write(f"[bold red]Invalid ULID:[/bold red] {info.get('error')}")
            return

        log.write(f"[bold]ULID:[/bold] {info['ulid']}")
        log.write(f"Timestamp: {info['timestamp']}")
        log.write(f"Date: {info['datetime']}")
        log.write(f"Randomness: {info['randomness']}")
        log.write(f"Hex: {info['hex']}")
        log.write(f"Int: {info['int']}")
        log.write(f"UUID: {info['uuid']}")

    @on(Button.Pressed, "#btn-ulid-validate")
    def on_validate(self) -> None:
        val = self.query_one("#input-ulid-validate", Input).value.strip()
        lbl = self.query_one("#lbl-ulid-validate-result", Static)

        if not val:
            lbl.update("Please enter a ULID.")
            return

        if self.manager.validate(val):
            lbl.update("[bold green]✅ Valid ULID[/bold green]")
        else:
            lbl.update("[bold red]❌ Invalid ULID[/bold red]")
