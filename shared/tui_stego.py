from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Button, Label, Input, TextArea, TabbedContent, TabPane
from shared.stego_lab import StegoLabManager
from pathlib import Path


class StegoLabTab(Container):
    """Tab for Image Steganography (Encode/Decode text in images)."""

    DEFAULT_CSS = """
    StegoLabTab {
        layout: vertical;
        height: 100%;
    }

    .stego-pane {
        height: 1fr;
        border: solid $accent;
        margin: 1;
        padding: 1;
    }

    .control-pane {
        height: auto;
        min-height: 15;
        border: solid $secondary;
        margin: 1;
        padding: 1;
    }

    .stat-box {
        background: $boost;
        padding: 1;
        margin-bottom: 1;
    }

    Button {
        margin: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = StegoLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Steganography Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                with TabPane("Encode"):
                    with Vertical(classes="stego-pane"):
                        yield Label("Input Image Path:")
                        yield Input(placeholder="/path/to/input.png", id="stego-encode-input-image")

                        yield Label("Text to Hide:")
                        yield TextArea(id="stego-encode-text")

                        yield Label("Output Image Path (PNG recommended):")
                        yield Input(placeholder="/path/to/output.png", id="stego-encode-output-image")

                        yield Button("Encode", id="btn-stego-encode", variant="primary")
                        yield Label("", id="lbl-stego-encode-result")

                with TabPane("Decode"):
                    with Vertical(classes="stego-pane"):
                        yield Label("Image Path (with hidden text):")
                        yield Input(placeholder="/path/to/encoded.png", id="stego-decode-input-image")

                        yield Button("Decode", id="btn-stego-decode", variant="primary")

                        yield Label("Extracted Text:")
                        yield TextArea(id="stego-decode-result", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if not btn_id:
            return

        if btn_id == "btn-stego-encode":
            await self.encode()
        elif btn_id == "btn-stego-decode":
            await self.decode()

    async def encode(self) -> None:
        input_image = self.query_one("#stego-encode-input-image", Input).value
        text = self.query_one("#stego-encode-text", TextArea).text
        output_image = self.query_one("#stego-encode-output-image", Input).value
        lbl_result = self.query_one("#lbl-stego-encode-result", Label)

        if not input_image or not text or not output_image:
            lbl_result.update("[red]Please provide all fields (Input Image, Text, Output Image).[/red]")
            return

        try:
            input_path = Path(input_image)
            output_path = Path(output_image)

            self.manager.encode(input_path, text, output_path)
            lbl_result.update("[green]Encoding successful![/green]")
            self.notify("Successfully encoded text into image.", severity="information")
        except Exception as e:
            lbl_result.update(f"[red]Error: {e}[/red]")
            self.notify(f"Failed to encode: {e}", severity="error")

    async def decode(self) -> None:
        input_image = self.query_one("#stego-decode-input-image", Input).value
        result_area = self.query_one("#stego-decode-result", TextArea)

        if not input_image:
            self.notify("Please provide the image path.", severity="warning")
            return

        try:
            input_path = Path(input_image)
            text = self.manager.decode(input_path)
            result_area.text = text
            self.notify("Decoding successful.", severity="information")
        except Exception as e:
            result_area.text = f"Error: {e}"
            self.notify(f"Failed to decode: {e}", severity="error")
