from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Static, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on

try:
    from shared.typeid_lab import TypeIDLabManager, HAS_TYPEID
except ImportError:
    HAS_TYPEID = False

class TypeIDLabTab(Container):
    """Tab for generating and parsing TypeIDs."""

    def compose(self) -> ComposeResult:
        with Vertical(id="typeid-container", classes="lab-container"):
            yield Label("[bold]TypeID Lab[/bold]", classes="welcome-text")
            yield Label("Generate and parse type-safe, K-sortable, globally unique identifiers.", classes="subtitle")

            with Horizontal(id="typeid-gen-section"):
                with Vertical(classes="section-box"):
                    yield Label("[bold]Generate TypeIDs[/bold]")
                    with Horizontal(classes="input-group"):
                        yield Label("Prefix:")
                        yield Input(id="typeid-prefix", placeholder="e.g. user", value="")
                    with Horizontal(classes="input-group"):
                        yield Label("Count:")
                        yield Input(id="typeid-count", placeholder="1", type="integer", value="1")
                    yield Button("Generate", id="btn-typeid-generate", variant="success")
                    yield Static("", id="typeid-gen-output", classes="output-box")

            with Horizontal(id="typeid-parse-section"):
                with Vertical(classes="section-box"):
                    yield Label("[bold]Parse TypeID[/bold]")
                    yield Input(placeholder="e.g. user_01h455vb4pex5vsknk084sn02q", id="typeid-parse-input")
                    yield Button("Parse", id="btn-typeid-parse", variant="primary")
                    yield RichLog(id="typeid-parse-result", wrap=True, markup=True)

    def on_mount(self) -> None:
        if not HAS_TYPEID:
            error_msg = "Error: typeid-python library not installed. Please install it using 'pip install typeid-python'."
            self.query_one("#typeid-gen-output", Static).update(error_msg)
            self.query_one("#typeid-parse-result", RichLog).write(f"[red]{error_msg}[/red]")

    @on(Button.Pressed, "#btn-typeid-generate")
    def on_generate_pressed(self) -> None:
        if not HAS_TYPEID:
            return

        try:
            manager = TypeIDLabManager()
        except ImportError as e:
            self.query_one("#typeid-gen-output", Static).update(f"Error: {e}")
            return

        prefix = self.query_one("#typeid-prefix", Input).value.strip()
        count_str = self.query_one("#typeid-count", Input).value

        try:
            count = int(count_str) if count_str.strip() else 1
            if count < 1:
                self.query_one("#typeid-gen-output", Static).update("Error: Count must be greater than 0.")
                return
        except ValueError:
            self.query_one("#typeid-gen-output", Static).update("Error: Count must be an integer.")
            return

        try:
            results = manager.generate(prefix=prefix, count=count)
            formatted_results = "\n".join([f"[bold green]{r}[/bold green]" for r in results])
            self.query_one("#typeid-gen-output", Static).update(f"Generated TypeID(s):\n{formatted_results}")
        except Exception as e:
            self.query_one("#typeid-gen-output", Static).update(f"Error: {e}")

    @on(Button.Pressed, "#btn-typeid-parse")
    def on_parse_pressed(self) -> None:
        if not HAS_TYPEID:
            return

        typeid_str = self.query_one("#typeid-parse-input", Input).value.strip()
        result_log = self.query_one("#typeid-parse-result", RichLog)
        result_log.clear()

        if not typeid_str:
            result_log.write("[red]Please enter a TypeID.[/red]")
            return

        try:
            manager = TypeIDLabManager()
        except ImportError as e:
            result_log.write(f"[red]Error: {e}[/red]")
            return

        info = manager.parse(typeid_str)
        if info["valid"]:
            result_log.write(f"[bold green]Valid TypeID[/bold green]")
            result_log.write(f"[blue]Prefix:[/blue] {info['prefix']}")
            result_log.write(f"[cyan]UUID:[/cyan] {info['uuid']}")
        else:
            result_log.write(f"[bold red]Invalid TypeID[/bold red]")
            result_log.write(f"Error: {info.get('error')}")
