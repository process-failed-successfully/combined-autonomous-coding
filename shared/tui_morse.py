from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea, Input
from shared.morse_lab import MorseLabManager


class MorseLabTab(Container):
    """Tab for Morse Code Encoding/Decoding and Audio generation."""

    DEFAULT_CSS = """
    MorseLabTab {
        layout: vertical;
        height: 100%;
    }

    .morse-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #morse-input, #morse-output {
        height: 1fr;
    }
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = MorseLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Morse Code Lab[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="morse-box"):
                yield Label("Input Text (or Morse to Decode):")
                yield TextArea(id="morse-input", show_line_numbers=False)

            # Controls Section
            with Horizontal(classes="morse-box"):
                yield Button("Encode", id="btn-morse-encode", variant="primary")
                yield Button("Decode", id="btn-morse-decode", variant="success")
                yield Button("Swap", id="btn-morse-swap", variant="warning")
                yield Button("Clear", id="btn-morse-clear", variant="error")
                yield Label("WPM:")
                yield Input(value="15", id="morse-wpm", type="integer", classes="small-input")
                yield Button("Export Audio", id="btn-morse-audio", variant="default")

            # Output Section
            with Vertical(classes="morse-box"):
                yield Label("Output:")
                yield TextArea(id="morse-output", read_only=False, show_line_numbers=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-morse-encode":
            self.process(encode=True)
        elif event.button.id == "btn-morse-decode":
            self.process(encode=False)
        elif event.button.id == "btn-morse-swap":
            self.swap_content()
        elif event.button.id == "btn-morse-clear":
            self.clear_content()
        elif event.button.id == "btn-morse-audio":
            self.export_audio()

    def process(self, encode: bool) -> None:
        text = self.query_one("#morse-input", TextArea).text
        output_area = self.query_one("#morse-output", TextArea)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        try:
            if encode:
                result = self.manager.encode(text)
            else:
                result = self.manager.decode(text)

            output_area.text = result
            self.notify("Done.")
        except Exception as e:
            output_area.text = f"Error: {e}"
            self.notify(f"Exception: {e}", severity="error")

    def export_audio(self) -> None:
        # First check output area. If we encoded to output, it's there.
        # Otherwise, check input area if it looks like morse code.
        output_text = self.query_one("#morse-output", TextArea).text
        input_text = self.query_one("#morse-input", TextArea).text

        morse_text = ""
        if all(c in '.-/ \n\t' for c in output_text) and output_text:
            morse_text = output_text
        elif all(c in '.-/ \n\t' for c in input_text) and input_text:
            morse_text = input_text

        if not morse_text:
            self.notify("Please encode text to Morse code first.", severity="warning")
            return

        wpm_str = self.query_one("#morse-wpm", Input).value
        wpm = int(wpm_str) if wpm_str.isdigit() else 15

        out_path = self.project_dir / "morse_output.wav"

        success = self.manager.generate_audio(morse_text, out_path, wpm=wpm)
        if success:
            self.notify(f"Audio exported to {out_path.name}", severity="information")
        else:
            self.notify("Failed to export audio.", severity="error")

    def swap_content(self) -> None:
        input_area = self.query_one("#morse-input", TextArea)
        output_area = self.query_one("#morse-output", TextArea)

        temp = input_area.text
        input_area.text = output_area.text
        output_area.text = temp
        self.notify("Swapped Input and Output.")

    def clear_content(self) -> None:
        self.query_one("#morse-input", TextArea).text = ""
        self.query_one("#morse-output", TextArea).text = ""
        self.notify("Cleared.")
