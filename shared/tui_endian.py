import sys
import struct
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Input, Button, Select, RadioSet, RadioButton, Static
from textual import on
from shared.endian_lab import EndianManager

class EndianLabTab(Container):
    """Tab for Endian Lab."""

    def __init__(self, project_dir: Path = Path("."), **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = EndianManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Endian Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield RadioSet(
                    RadioButton("Hex String Swap", id="radio-hex", value=True),
                    RadioButton("Integer Swap", id="radio-int"),
                    id="radio-mode"
                )

            # Hex Swap Section
            with Vertical(id="section-hex", classes="stat-box"):
                yield Label("Hex String (e.g. 0xAABBCCDD)")
                yield Input(placeholder="0x12345678", id="input-hex")
                yield Button("Swap Endianness", id="btn-swap-hex", variant="primary")
                yield Static("Result: ", id="result-hex", classes="box")

            # Integer Swap Section
            with Vertical(id="section-int", classes="stat-box"):
                yield Label("Integer Value (Dec, Hex, or Oct)")
                yield Input(placeholder="305419896 or 0x12345678", id="input-int")
                yield Label("Bit Size")
                yield Select.from_values([16, 32, 64], value=32, id="select-bits")
                yield Button("Swap Endianness", id="btn-swap-int", variant="primary")
                yield Static("Result: ", id="result-int", classes="box")

    def on_mount(self) -> None:
        self.query_one("#section-int").display = False

    @on(RadioSet.Changed, "#radio-mode")
    def on_mode_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed.id == "radio-hex":
            self.query_one("#section-hex").display = True
            self.query_one("#section-int").display = False
        else:
            self.query_one("#section-hex").display = False
            self.query_one("#section-int").display = True

    @on(Button.Pressed, "#btn-swap-hex")
    def on_swap_hex(self) -> None:
        val = self.query_one("#input-hex", Input).value.strip()
        if not val:
            self.notify("Hex string required", severity="error")
            return

        try:
            swapped = self.manager.hex_swap(val)
            self.query_one("#result-hex", Static).update(f"Result: [bold green]{swapped}[/bold green]")
        except Exception as e:
            self.query_one("#result-hex", Static).update(f"Error: [bold red]{e}[/bold red]")

    @on(Button.Pressed, "#btn-swap-int")
    def on_swap_int(self) -> None:
        val_str = self.query_one("#input-int", Input).value.strip()
        bits = self.query_one("#select-bits", Select).value

        if not val_str:
            self.notify("Integer value required", severity="error")
            return

        try:
            val = int(val_str, 0)
        except ValueError:
            self.query_one("#result-int", Static).update("Error: [bold red]Invalid integer format[/bold red]")
            return

        try:
            swapped = self.manager.int_swap(val, bits)
            self.query_one("#result-int", Static).update(
                f"Original: {val} ({hex(val)})\nResult:   [bold green]{swapped} ({hex(swapped)})[/bold green]"
            )
        except Exception as e:
            self.query_one("#result-int", Static).update(f"Error: [bold red]{e}[/bold red]")
