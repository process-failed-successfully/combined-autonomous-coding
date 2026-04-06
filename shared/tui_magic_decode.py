from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, RichLog, Label
from textual.screen import Screen
from shared.magic_decode_lab import MagicDecodeManager

class MagicDecodeTab(Vertical):
    """TUI tab for Magic Decode Lab."""

    def compose(self) -> ComposeResult:
        with Vertical(id="magic-decode-container"):
            yield Label("Magic Decode Lab - Enter an opaque string to auto-decode it", classes="header-label")
            with Horizontal(id="magic-decode-input-container", classes="input-row"):
                yield Input(id="magic-decode-input", placeholder="Enter string (Base64, Hex, URL, JWT, etc.)")
                yield Button("Decode", id="magic-decode-btn", variant="primary")

            yield Label("Results:")
            yield RichLog(id="magic-decode-results", highlight=True, markup=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "magic-decode-btn":
            self.action_decode()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "magic-decode-input":
            self.action_decode()

    def action_decode(self) -> None:
        input_widget = self.query_one("#magic-decode-input", Input)
        log_widget = self.query_one("#magic-decode-results", RichLog)

        text = input_widget.value.strip()
        if not text:
            log_widget.clear()
            log_widget.write("[red]Please enter a string to decode.[/red]")
            return

        manager = MagicDecodeManager()
        results = manager.decode(text)

        log_widget.clear()

        if not results:
            log_widget.write("[yellow]No decodings found. The string might not be in a recognized format or is just plain text.[/yellow]")
            return

        log_widget.write("[bold cyan]Magic Decode Results:[/bold cyan]\n")
        for format_name, decoded_val in results.items():
            log_widget.write(f"[bold green]--- {format_name} ---[/bold green]")
            log_widget.write(decoded_val)
            log_widget.write("")
