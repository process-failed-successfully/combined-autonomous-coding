from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input, Select
from textual import on
from shared.endian_lab import EndianManager

class EndianLabTab(Container):
    """Tab for Endianness Conversion (Little <-> Big)."""

    DEFAULT_CSS = """
    EndianLabTab {
        layout: vertical;
        height: 100%;
        overflow-y: auto;
    }

    .endian-section {
        border: solid $accent;
        padding: 1;
        margin: 1;
        height: auto;
    }

    .endian-row {
        height: auto;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Endian Lab (Little <-> Big Endian Converter)[/bold]", classes="welcome-text")

            # Hex Converter
            with Vertical(classes="endian-section"):
                yield Label("Hex String Conversion")
                yield Input(placeholder="Enter hex string (e.g. 11223344 or 0x11223344)", id="endian-hex-input")
                with Horizontal(classes="endian-row"):
                    yield Button("Swap Endianness", id="btn-endian-hex", variant="primary")
                yield Input(placeholder="Result", id="endian-hex-output", read_only=True)

            # Integer Converter
            with Vertical(classes="endian-section"):
                yield Label("Integer Conversion")
                with Horizontal(classes="endian-row"):
                    yield Input(placeholder="Enter integer", id="endian-int-input")
                    yield Select(
                        [( "16-bit (2 bytes)", 2), ("32-bit (4 bytes)", 4), ("64-bit (8 bytes)", 8)],
                        prompt="Select Size",
                        id="endian-int-size",
                        value=4
                    )
                with Horizontal(classes="endian-row"):
                    yield Button("Swap Endianness", id="btn-endian-int", variant="primary")
                yield Input(placeholder="Result", id="endian-int-output", read_only=True)


    @on(Button.Pressed)
    def handle_button_pressed(self, event: Button.Pressed) -> None:
        manager = EndianManager()

        if event.button.id == "btn-endian-hex":
            hex_input = self.query_one("#endian-hex-input", Input).value.strip()
            out_area = self.query_one("#endian-hex-output", Input)
            if not hex_input:
                self.notify("Input empty.", severity="warning")
                return
            try:
                result = manager.convert_hex(hex_input)
                out_area.value = result
                self.notify("Converted.")
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

        elif event.button.id == "btn-endian-int":
            int_input_str = self.query_one("#endian-int-input", Input).value.strip()
            size = self.query_one("#endian-int-size", Select).value
            out_area = self.query_one("#endian-int-output", Input)

            if not int_input_str:
                self.notify("Input empty.", severity="warning")
                return
            if not size:
                self.notify("Select a size.", severity="warning")
                return

            try:
                val = int(int_input_str)
                result = manager.convert_int(val, int(size))
                out_area.value = str(result)
                self.notify("Converted.")
            except ValueError:
                self.notify("Invalid integer.", severity="error")
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")
