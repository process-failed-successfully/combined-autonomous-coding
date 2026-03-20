from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, TextArea
from shared.stego_lab import StegoManager
from pathlib import Path


class StegoLabTab(Container):
    """Tab for Steganography (LSB Hiding/Extracting)."""

    DEFAULT_CSS = """
    StegoLabTab {
        layout: vertical;
        height: 100%;
        overflow-y: auto;
    }

    .stego-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .stego-inputs {
        height: auto;
    }

    #stego-input-text, #stego-output-text {
        height: 1fr;
        min-height: 5;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Steganography Lab (Hide/Extract Text in Images)[/bold]", classes="welcome-text")

            # Hide Section
            with Vertical(classes="stego-box"):
                yield Label("[bold]Hide Text[/bold]")
                with Vertical(classes="stego-inputs"):
                    yield Input(placeholder="Source Image Path (e.g., input.png)", id="stego-hide-img")
                    yield Input(placeholder="Output Image Path (e.g., output.png)", id="stego-hide-out")
                yield Label("Text to Hide:")
                yield TextArea(id="stego-input-text", show_line_numbers=False)
                with Horizontal():
                    yield Button("Hide Text", id="btn-stego-hide", variant="primary")

            # Extract Section
            with Vertical(classes="stego-box"):
                yield Label("[bold]Extract Text[/bold]")
                with Vertical(classes="stego-inputs"):
                    yield Input(placeholder="Image Path with Hidden Text (e.g., output.png)", id="stego-extract-img")
                with Horizontal():
                    yield Button("Extract Text", id="btn-stego-extract", variant="success")
                yield Label("Extracted Text:")
                yield TextArea(id="stego-output-text", read_only=True, show_line_numbers=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-stego-hide":
            self.hide_text()
        elif event.button.id == "btn-stego-extract":
            self.extract_text()

    def hide_text(self) -> None:
        img_path = self.query_one("#stego-hide-img", Input).value.strip()
        out_path = self.query_one("#stego-hide-out", Input).value.strip()
        text = self.query_one("#stego-input-text", TextArea).text

        if not img_path or not out_path or not text:
            self.notify("Please provide source image path, output image path, and text to hide.", severity="warning")
            return

        if not Path(img_path).is_file():
            self.notify(f"Source image '{img_path}' not found.", severity="error")
            return

        try:
            manager = StegoManager()
            manager.hide_text(img_path, text, out_path)
            self.notify(f"Text successfully hidden in '{out_path}'.", severity="information")
        except Exception as e:
            self.notify(f"Error hiding text: {e}", severity="error")

    def extract_text(self) -> None:
        img_path = self.query_one("#stego-extract-img", Input).value.strip()
        output_area = self.query_one("#stego-output-text", TextArea)

        if not img_path:
            self.notify("Please provide the image path to extract text from.", severity="warning")
            return

        if not Path(img_path).is_file():
            self.notify(f"Image '{img_path}' not found.", severity="error")
            return

        try:
            manager = StegoManager()
            extracted = manager.extract_text(img_path)
            if extracted:
                output_area.text = extracted
                self.notify("Text extracted successfully.", severity="information")
            else:
                output_area.text = ""
                self.notify("No text could be extracted or the hidden text was empty.", severity="warning")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Error extracting text: {e}", severity="error")
