from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, TextArea, Button, Select, RichLog
from textual import on

from shared.asn1_lab import Asn1LabManager

class Asn1LabTab(Container):
    """Tab for ASN.1 decoding operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Asn1LabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]ASN.1 Lab[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("Input (PEM, Base64, or Hex):")
                yield TextArea(id="asn1-input", show_line_numbers=True)

                with Horizontal():
                    yield Label("Format:", classes="label")
                    yield Select.from_values(
                        ["auto", "pem", "base64", "hex"],
                        id="asn1-format",
                        value="auto"
                    )
                    yield Button("Decode", id="btn-asn1-decode", variant="primary")

            with Vertical(classes="stat-box"):
                yield Label("Decoded Output:")
                yield RichLog(id="asn1-output", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-asn1-decode")
    def on_decode_pressed(self) -> None:
        payload = self.query_one("#asn1-input", TextArea).text
        input_format = str(self.query_one("#asn1-format", Select).value)
        output_log = self.query_one("#asn1-output", RichLog)

        if not payload.strip():
            output_log.write("[bold red]Error: Input cannot be empty.[/bold red]")
            return

        result = self.manager.decode(payload, input_format=input_format)

        output_log.clear()
        if result["success"]:
            output_log.write("[bold green]Decoding Successful:[/bold green]\n")
            output_log.write(result["output"])
        else:
            output_log.write(f"[bold red]Error: {result['error']}[/bold red]")
