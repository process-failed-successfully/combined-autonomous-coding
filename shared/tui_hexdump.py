import os
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.widgets import TabPane, Input, Button, Label, RichLog, RadioSet, RadioButton
from textual import on, work
from textual.message import Message

from shared.hexdump_lab import HexdumpManager


class HexdumpLabTab(TabPane):
    """A TUI tab for Hexdump Lab."""

    def __init__(self, id: str = "tab-hexdump", classes: str = ""):
        super().__init__("Hexdump Lab", id=id, classes=classes)
        self.manager = HexdumpManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("Generate Hex Dump", classes="section-header")

            with Horizontal():
                with RadioSet(id="hexdump-source-type"):
                    yield RadioButton("Text Input", id="hexdump-type-text", value=True)
                    yield RadioButton("File Path", id="hexdump-type-file")

            yield Input(placeholder="Enter text or file path...", id="hexdump-input")

            with Horizontal(classes="controls-row"):
                yield Input(placeholder="Offset (e.g. 0)", value="0", id="hexdump-offset", type="integer", classes="number-input")
                yield Input(placeholder="Length (-1 for all)", value="-1", id="hexdump-length", type="integer", classes="number-input")

            with Horizontal(classes="controls-row"):
                yield Button("Generate Dump", id="hexdump-generate-btn", variant="primary")
                yield Button("Clear Output", id="hexdump-clear-btn", variant="error")

            yield Label("Hex Dump Output:")
            yield RichLog(id="hexdump-output", wrap=False, highlight=True, markup=True)

    @on(Button.Pressed, "#hexdump-generate-btn")
    def on_generate_pressed(self, event: Button.Pressed) -> None:
        """Handle generate button press."""
        input_widget = self.query_one("#hexdump-input", Input)
        offset_widget = self.query_one("#hexdump-offset", Input)
        length_widget = self.query_one("#hexdump-length", Input)
        type_radio = self.query_one("#hexdump-source-type", RadioSet)
        output_log = self.query_one("#hexdump-output", RichLog)

        val = input_widget.value.strip()

        try:
            offset = int(offset_widget.value) if offset_widget.value else 0
            length = int(length_widget.value) if length_widget.value else -1
        except ValueError:
            output_log.write("[bold red]Error: Offset and Length must be integers.[/bold red]")
            return

        if not val:
             output_log.write("[bold red]Error: Input cannot be empty.[/bold red]")
             return

        data = b""
        if type_radio.pressed_button and type_radio.pressed_button.id == "hexdump-type-file":
             p = Path(val)
             if not p.is_file():
                  output_log.write(f"[bold red]Error: File '{val}' not found.[/bold red]")
                  return
             try:
                 with open(p, "rb") as f:
                     if offset > 0:
                         f.seek(offset)
                     if length >= 0:
                         data = f.read(length)
                     else:
                         data = f.read()
             except Exception as e:
                 output_log.write(f"[bold red]Error reading file: {e}[/bold red]")
                 return
        else:
             # Text mode
             text_data = val.encode("utf-8")
             start = max(0, offset)
             if length >= 0:
                  data = text_data[start:start + length]
             else:
                  data = text_data[start:]

        try:
            # Hexdump manager offset parameter is just for labeling rows
            # We already truncated the data above correctly.
            # But the label offset should match the actual file offset if requested.
            result = self.manager.hexdump(data, offset=offset)
            output_log.write(f"[bold green]--- Hex Dump ---[/bold green]")
            output_log.write(result)
        except Exception as e:
            output_log.write(f"[bold red]Error generating hexdump: {e}[/bold red]")


    @on(Button.Pressed, "#hexdump-clear-btn")
    def on_clear_pressed(self, event: Button.Pressed) -> None:
        """Handle clear button press."""
        output_log = self.query_one("#hexdump-output", RichLog)
        output_log.clear()
