from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Input, Button, Static
import traceback


class SqidsLabTab(Container):
    """A TUI tab for Sqids encoding and decoding."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from shared.sqids_lab import HAS_SQIDS
        self.has_sqids = HAS_SQIDS
        self.error_message = None
        if not self.has_sqids:
            self.error_message = "Error: 'sqids' module not installed. Please 'pip install sqids'."

    def compose(self) -> ComposeResult:
        if not self.has_sqids:
            yield Static(self.error_message, id="error_message", classes="error-text")
            return

        yield Static("Sqids Lab - Encode and Decode Array of Numbers", classes="tab-title")

        # Encode Section
        yield Static("Encode: Comma-separated Numbers -> Sqid", classes="section-title")
        yield Input(placeholder="e.g., 1, 2, 3", id="input_numbers")
        with Horizontal(classes="button-group"):
            yield Button("Encode", id="btn_encode", variant="primary")
        yield Input(placeholder="Encoded result...", id="output_encoded", disabled=True)

        yield Static("")

        # Decode Section
        yield Static("Decode: Sqid -> Comma-separated Numbers", classes="section-title")
        yield Input(placeholder="e.g., 86Rf07", id="input_sqid")
        with Horizontal(classes="button-group"):
            yield Button("Decode", id="btn_decode")
        yield Input(placeholder="Decoded result...", id="output_decoded", disabled=True)

        yield Static("", id="sqids_status_message", classes="status-message")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.has_sqids:
            return

        from shared.sqids_lab import SqidsManager
        status_msg = self.query_one("#sqids_status_message", Static)
        status_msg.update("")

        if event.button.id == "btn_encode":
            input_widget = self.query_one("#input_numbers", Input)
            output_widget = self.query_one("#output_encoded", Input)
            val = input_widget.value.strip()

            if not val:
                status_msg.update("[red]Error: Input numbers cannot be empty.[/red]")
                output_widget.value = ""
                return

            try:
                numbers = [int(x.strip()) for x in val.split(',')]
                encoded = SqidsManager.encode(numbers)
                output_widget.value = encoded
                status_msg.update("[green]Encoded successfully.[/green]")
            except ValueError:
                status_msg.update("[red]Error: Please enter a valid comma-separated list of positive integers.[/red]")
                output_widget.value = ""
            except Exception as e:
                status_msg.update(f"[red]Error: {str(e)}[/red]")
                output_widget.value = ""

        elif event.button.id == "btn_decode":
            input_widget = self.query_one("#input_sqid", Input)
            output_widget = self.query_one("#output_decoded", Input)
            val = input_widget.value.strip()

            if not val:
                status_msg.update("[red]Error: Input Sqid cannot be empty.[/red]")
                output_widget.value = ""
                return

            try:
                decoded = SqidsManager.decode(val)
                if not decoded:
                    status_msg.update("[red]Error: Invalid sqid or no numbers decoded.[/red]")
                    output_widget.value = ""
                else:
                    output_widget.value = ",".join(str(n) for n in decoded)
                    status_msg.update("[green]Decoded successfully.[/green]")
            except Exception as e:
                status_msg.update(f"[red]Error: {str(e)}[/red]")
                output_widget.value = ""
