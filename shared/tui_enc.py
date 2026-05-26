"""
Encoding Lab TUI Tab
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Input, Button, RichLog, Select

from shared.enc_lab import EncLabManager

class EncLabTab(Vertical):
    """TUI Tab for Encoding operations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = EncLabManager()

    def compose(self) -> ComposeResult:
        yield Label("Encoding Lab", classes="section-title")

        with Horizontal(classes="input-group"):
            yield Label("Algorithm:")
            algorithms = [("Base64", "base64"), ("URL", "url"), ("HTML Entities", "html"), ("Hex", "hex"), ("Rot13", "rot13")]
            yield Select(algorithms, id="enc-algo-select", value="base64")

        with Horizontal(classes="input-group"):
            yield Label("Operation:")
            operations = [("Encode", "encode"), ("Decode", "decode")]
            yield Select(operations, id="enc-op-select", value="encode")

        with Horizontal(classes="input-group"):
            yield Label("Input Text:")
            yield Input(placeholder="Enter text to process", id="enc-input")

        with Horizontal(classes="button-group"):
            yield Button("Process", id="btn-enc-process", variant="primary")
            yield Button("Clear Log", id="btn-enc-clear")

        yield RichLog(id="enc-log", highlight=True, markup=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one("#enc-log", RichLog)

        if event.button.id == "btn-enc-clear":
            log.clear()
            return

        if event.button.id == "btn-enc-process":
            algo = self.query_one("#enc-algo-select", Select).value
            operation = self.query_one("#enc-op-select", Select).value
            text = self.query_one("#enc-input", Input).value.strip()

            if not text:
                log.write("[red]Error: Input text required.[/red]")
                return

            decode = (operation == "decode")

            try:
                if algo == "base64":
                    result = self.manager.base64_process(text, decode=decode)
                elif algo == "url":
                    result = self.manager.url_process(text, decode=decode)
                elif algo == "html":
                    result = self.manager.html_process(text, decode=decode)
                elif algo == "hex":
                    result = self.manager.hex_process(text, decode=decode)
                elif algo == "rot13":
                    result = self.manager.rot13_process(text)
                else:
                    log.write(f"[red]Error: Unknown algorithm {algo}[/red]")
                    return

                log.write(f"[green]Success ({operation} via {algo}):[/green]")
                log.write(result)

            except Exception as e:
                log.write(f"[red]Error: {e}[/red]")
