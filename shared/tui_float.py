import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, Select, Input, RadioSet, RadioButton
from textual import on
from shared.float_lab import FloatLabManager

class FloatLabTab(Container):
    """
    TUI for Float Lab (IEEE 754 Converter).
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = FloatLabManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]IEEE 754 Floating-Point Converter[/bold]", classes="welcome-text")

            with Container(classes="stat-box"):
                yield Label("Mode:")
                with RadioSet(id="rs-float-mode"):
                    yield RadioButton("Encode (Float -> IEEE 754)", id="rb-encode", value=True)
                    yield RadioButton("Decode (IEEE 754 Hex -> Float)", id="rb-decode")

                yield Label("Precision:")
                with RadioSet(id="rs-float-precision"):
                    yield RadioButton("Single (32-bit)", id="rb-single", value=True)
                    yield RadioButton("Double (64-bit)", id="rb-double")

                yield Label("Input:", id="lbl-float-input")
                yield Input(id="input-float", placeholder="Enter float value (e.g., -12.5)")

                with Horizontal():
                    yield Button("Convert", id="btn-float-convert", variant="primary")

            with Container(classes="stat-box"):
                yield Label("[bold]Result[/bold]")
                yield Label("Value:", classes="stat-label")
                yield Input(id="out-float-value", disabled=True)
                yield Label("Hexadecimal:", classes="stat-label")
                yield Input(id="out-float-hex", disabled=True)
                yield Label("Binary (Sign | Exponent | Mantissa):", classes="stat-label")
                yield Input(id="out-float-bin", disabled=True)

    @on(RadioSet.Changed, "#rs-float-mode")
    def on_mode_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed.id == "rb-encode":
            self.query_one("#lbl-float-input", Label).update("Input (Float):")
            self.query_one("#input-float", Input).placeholder = "Enter float value (e.g., -12.5)"
        else:
            self.query_one("#lbl-float-input", Label).update("Input (Hex):")
            self.query_one("#input-float", Input).placeholder = "Enter hex string (e.g., c1480000)"

    @on(Button.Pressed, "#btn-float-convert")
    def on_convert(self) -> None:
        mode = "encode" if self.query_one("#rb-encode", RadioButton).value else "decode"
        precision = "single" if self.query_one("#rb-single", RadioButton).value else "double"
        input_val = self.query_one("#input-float", Input).value.strip()

        if not input_val:
            self.notify("Input cannot be empty", severity="error")
            return

        if mode == "encode":
            try:
                val = float(input_val)
            except ValueError:
                self.notify("Invalid float value", severity="error")
                return
            res = self.manager.encode(val, precision)
        else:
            res = self.manager.decode(input_val, precision)

        if res["success"]:
            self.query_one("#out-float-value", Input).value = str(res["value"])
            self.query_one("#out-float-hex", Input).value = res["hex"]
            self.query_one("#out-float-bin", Input).value = res["bin"]
            self.notify("Conversion successful", severity="information")
        else:
            self.notify(f"Error: {res['error']}", severity="error")
