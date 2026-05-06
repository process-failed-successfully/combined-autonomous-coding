from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Select, RichLog, TabbedContent, TabPane, Static
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from shared.uuid_lab import UuidLabManager

class UuidLabTab(Container):
    """Tab for UUID operations (Generate, Inspect, Validate)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = UuidLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]UUID Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Generate Tab
                with TabPane("Generate"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Generate UUIDs[/bold]")

                        with Horizontal():
                            yield Label("Version:")
                            yield Select.from_values([1, 3, 4, 5, 7], id="select-uuid-version", value=4)
                            yield Label("Count:")
                            yield Input(placeholder="1", id="input-uuid-count", type="integer", value="1")

                        # Inputs for v3/v5
                        with Vertical(id="container-uuid-ns-name", classes="hidden"):
                            yield Label("Namespace (UUID, DNS, URL, OID, X500):")
                            yield Input(placeholder="e.g. DNS or a UUID string", id="input-uuid-namespace")
                            yield Label("Name:")
                            yield Input(placeholder="e.g. example.com", id="input-uuid-name")

                        yield Button("Generate", id="btn-uuid-generate", variant="primary")

                        yield Label("[bold]Output:[/bold]")
                        yield RichLog(id="log-uuid-generate", wrap=True, highlight=True, markup=True)

                # Inspect Tab
                with TabPane("Inspect"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Inspect UUID[/bold]")
                        with Horizontal():
                            yield Input(placeholder="Enter UUID...", id="input-uuid-inspect")
                            yield Button("Inspect", id="btn-uuid-inspect", variant="warning")

                        yield Label("[bold]Details:[/bold]")
                        yield RichLog(id="log-uuid-inspect", wrap=True, highlight=True, markup=True)

                # Validate Tab
                with TabPane("Validate"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Validate UUID[/bold]")
                        with Horizontal():
                            yield Input(placeholder="Enter UUID...", id="input-uuid-validate")
                            yield Button("Validate", id="btn-uuid-validate", variant="success")

                        yield Static(id="lbl-uuid-validate-result", classes="result-box")

    def on_mount(self) -> None:
        # Initial UI state check
        self.toggle_ns_inputs()

    @on(Select.Changed, "#select-uuid-version")
    def on_version_changed(self, event: Select.Changed) -> None:
        self.toggle_ns_inputs()

    def toggle_ns_inputs(self) -> None:
        ver = self.query_one("#select-uuid-version", Select).value
        container = self.query_one("#container-uuid-ns-name", Vertical)

        if ver in [3, 5]:
            container.remove_class("hidden")
        else:
            container.add_class("hidden")

    @on(Button.Pressed, "#btn-uuid-generate")
    def on_generate(self) -> None:
        ver = self.query_one("#select-uuid-version", Select).value
        count_val = self.query_one("#input-uuid-count", Input).value
        count = int(count_val) if count_val.isdigit() else 1

        ns = self.query_one("#input-uuid-namespace", Input).value
        name = self.query_one("#input-uuid-name", Input).value

        log = self.query_one("#log-uuid-generate", RichLog)
        log.clear()

        try:
            results = self.manager.generate(
                version=ver,
                count=count,
                namespace=ns if ver in [3, 5] else None,
                name=name if ver in [3, 5] else None
            )
            for u in results:
                log.write(f"[green]{u}[/green]")
            self.notify(f"Generated {len(results)} UUIDs.")
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify("Generation failed.", severity="error")

    @on(Button.Pressed, "#btn-uuid-inspect")
    def on_inspect(self) -> None:
        val = self.query_one("#input-uuid-inspect", Input).value.strip()
        log = self.query_one("#log-uuid-inspect", RichLog)
        log.clear()

        if not val:
            self.notify("Please enter a UUID.", severity="warning")
            return

        info = self.manager.inspect(val)
        if not info["valid"]:
            log.write(f"[bold red]Invalid UUID:[/bold red] {info.get('error')}")
            return

        log.write(f"[bold]UUID:[/bold] {info['uuid']}")
        log.write(f"Version: {info['version']}")
        log.write(f"Variant: {info['variant']}")
        log.write(f"Hex: {info['hex']}")

        if info.get("version") == 1:
            log.write(f"\n[bold]v1 Specifics:[/bold]")
            log.write(f"Time: {info.get('timestamp_iso', info.get('time'))}")
            log.write(f"Node (MAC): {info.get('mac')}")
            log.write(f"Clock Seq: {info.get('clock_seq')}")
        elif info.get("version") == 7:
            log.write(f"\n[bold]v7 Specifics:[/bold]")
            log.write(f"Time MS: {info.get('time_ms')} (Unix Epoch)")
            log.write(f"Date: {info.get('timestamp_iso')}")

        log.write(f"\nURN: {info['urn']}")

    @on(Button.Pressed, "#btn-uuid-validate")
    def on_validate(self) -> None:
        val = self.query_one("#input-uuid-validate", Input).value.strip()
        lbl = self.query_one("#lbl-uuid-validate-result", Static)

        if not val:
            lbl.update("Please enter a UUID.")
            return

        if self.manager.validate(val):
            lbl.update(f"[bold green]✅ Valid UUID[/bold green]")
        else:
            lbl.update(f"[bold red]❌ Invalid UUID[/bold red]")
