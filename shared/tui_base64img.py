import os
import base64
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, Input, TextArea
from textual.containers import VerticalScroll
from shared.base64img_lab import Base64ImgLabManager

class Base64ImgLabTab(VerticalScroll):
    """TUI tab for Base64Img Lab."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = Base64ImgLabManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-4"):
            yield Label("[bold cyan]Base64 Image Encoder/Decoder[/]")
            yield Label("Encode an image file to a Base64 string, or decode a Base64 string back to an image.", classes="mb-4 text-muted")

            with Horizontal(classes="mb-4 h-auto"):
                with Vertical(classes="w-1-2 pr-2"):
                    yield Label("[bold]Encode Image to Base64[/]", classes="mb-2")
                    yield Input(placeholder="Path to image file (e.g., image.png)", id="input-encode-path", classes="mb-2")
                    yield Button("Encode", id="btn-encode", variant="primary", classes="mb-2")
                    yield TextArea(id="output-base64", classes="h-32 mb-2")
                    yield Button("Copy to Clipboard", id="btn-copy-base64", classes="mb-2")
                    yield Label("", id="lbl-encode-status", classes="text-success")

                with Vertical(classes="w-1-2 pl-2"):
                    yield Label("[bold]Decode Base64 to Image[/]", classes="mb-2")
                    # TextArea in older textual doesn't take 'placeholder' in init
                    yield TextArea(id="input-decode-base64", classes="h-32 mb-2")
                    yield Input(placeholder="Output image path (e.g., decoded.png)", id="input-decode-output", classes="mb-2")
                    yield Button("Decode", id="btn-decode", variant="primary", classes="mb-2")
                    yield Label("", id="lbl-decode-status", classes="text-success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn-encode":
            self._handle_encode()
        elif button_id == "btn-decode":
            self._handle_decode()
        elif button_id == "btn-copy-base64":
            self._handle_copy_base64()

    def _handle_encode(self) -> None:
        input_path = self.query_one("#input-encode-path", Input).value.strip()
        status_lbl = self.query_one("#lbl-encode-status", Label)
        output_ta = self.query_one("#output-base64", TextArea)

        if not input_path:
            status_lbl.update("[red]Please provide a file path.[/red]")
            return

        result = self.manager.encode_image(input_path)
        if result["success"]:
            output_ta.text = result["result"]
            status_lbl.update("[green]Image successfully encoded.[/green]")
        else:
            status_lbl.update(f"[red]{result['error']}[/red]")

    def _handle_decode(self) -> None:
        base64_input = self.query_one("#input-decode-base64", TextArea).text.strip()
        output_path = self.query_one("#input-decode-output", Input).value.strip()
        status_lbl = self.query_one("#lbl-decode-status", Label)

        if not base64_input:
            status_lbl.update("[red]Please provide a Base64 string.[/red]")
            return

        if not output_path:
            status_lbl.update("[red]Please provide an output path.[/red]")
            return

        # Check if input is a file path
        if len(base64_input) < 1000 and os.path.exists(base64_input) and os.path.isfile(base64_input):
            try:
                with open(base64_input, "r") as f:
                    base64_input = f.read().strip()
            except Exception as e:
                status_lbl.update(f"[red]Error reading file: {e}[/red]")
                return

        result = self.manager.decode_image(base64_input, output_path)
        if result["success"]:
            status_lbl.update(f"[green]Image successfully saved to {output_path}.[/green]")
        else:
            status_lbl.update(f"[red]{result['error']}[/red]")

    def _handle_copy_base64(self) -> None:
        from shared.clipboard_lab import copy_to_clipboard
        text = self.query_one("#output-base64", TextArea).text
        status_lbl = self.query_one("#lbl-encode-status", Label)
        if text:
            if copy_to_clipboard(text):
                status_lbl.update("[green]Copied to clipboard![/green]")
            else:
                status_lbl.update("[red]Failed to copy to clipboard.[/red]")
        else:
            status_lbl.update("[red]Nothing to copy.[/red]")
