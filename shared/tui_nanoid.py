import nanoid
from textual.app import ComposeResult
from textual.widgets import Static, Input, Button, Label, RichLog
from textual.containers import VerticalScroll, Horizontal, Container

class NanoIDLabTab(Container):
    """TUI Tab for generating NanoIDs."""

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("NanoID Lab", classes="header-label")

            with Horizontal(classes="input-row"):
                yield Label("Size:")
                yield Input(value="21", id="input-size", placeholder="Length of NanoID (default 21)")

            with Horizontal(classes="input-row"):
                yield Label("Alphabet:")
                yield Input(value="", id="input-alphabet", placeholder="Custom alphabet (optional)")

            with Horizontal(classes="input-row"):
                yield Label("Count:")
                yield Input(value="1", id="input-count", placeholder="Number of NanoIDs to generate")

            yield Button("Generate NanoID", id="btn-generate", variant="primary")

            yield Static("Output:", classes="section-label")
            yield RichLog(id="log-output", markup=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-generate":
            self.generate_nanoids()

    def generate_nanoids(self) -> None:
        size_input = self.query_one("#input-size", Input).value.strip()
        alphabet_input = self.query_one("#input-alphabet", Input).value
        count_input = self.query_one("#input-count", Input).value.strip()
        log_view = self.query_one("#log-output", RichLog)

        log_view.clear()

        try:
            size = int(size_input) if size_input else 21
            if size <= 0:
                raise ValueError("Size must be greater than 0.")
        except ValueError:
            log_view.write("[red]Error: Size must be a valid positive integer.[/red]")
            return

        try:
            count = int(count_input) if count_input else 1
            if count <= 0:
                raise ValueError("Count must be greater than 0.")
        except ValueError:
            log_view.write("[red]Error: Count must be a valid positive integer.[/red]")
            return

        alphabet = alphabet_input if alphabet_input else None

        try:
            for _ in range(count):
                if alphabet:
                    # Provide size and alphabet
                    result = nanoid.generate(alphabet=alphabet, size=size)
                else:
                    # Use defaults or just custom size
                    result = nanoid.generate(size=size)
                log_view.write(f"[green]{result}[/green]")
        except Exception as e:
            log_view.write(f"[red]Generation Error: {e}[/red]")
