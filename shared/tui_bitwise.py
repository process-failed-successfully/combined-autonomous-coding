from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input, Select
from shared.bitwise_lab import BitwiseLabManager

class BitwiseLabTab(Container):
    """Tab for Bitwise Operations and Base Conversions."""

    DEFAULT_CSS = """
    BitwiseLabTab {
        layout: vertical;
        height: 100%;
        overflow-y: auto;
    }

    .bitwise-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    .bitwise-output-label {
        margin-top: 1;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = BitwiseLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Bitwise Lab (Base Converter & Bitwise Operations)[/bold]", classes="welcome-text")

            with Vertical(classes="bitwise-box"):
                yield Label("Operation:")
                yield Select(
                    [
                        ("Base Conversion", "convert"),
                        ("AND (&)", "and"),
                        ("OR (|)", "or"),
                        ("XOR (^)", "xor"),
                        ("NOT (~)", "not"),
                        ("Left Shift (<<)", "lshift"),
                        ("Right Shift (>>)", "rshift"),
                    ],
                    id="bitwise-operation-select",
                    value="convert"
                )

                yield Label("Number 1 (Prefix with 0x, 0b, or 0o for hex/bin/oct):")
                yield Input(placeholder="e.g., 42, 0x2A, 0b101010", id="bitwise-input-1")

                yield Label("Number 2 (Required for AND, OR, XOR, shifts):", id="bitwise-input-2-label")
                yield Input(placeholder="e.g., 10, 0xA", id="bitwise-input-2")

                with Horizontal():
                    yield Button("Execute", id="btn-bitwise-execute", variant="primary")

                yield Label("Error:", id="bitwise-error", classes="error-text")

                yield Label("Result (Decimal):", classes="bitwise-output-label")
                yield Input(id="bitwise-output-dec", disabled=True)

                yield Label("Result (Hex):", classes="bitwise-output-label")
                yield Input(id="bitwise-output-hex", disabled=True)

                yield Label("Result (Binary):", classes="bitwise-output-label")
                yield Input(id="bitwise-output-bin", disabled=True)

                yield Label("Result (Octal):", classes="bitwise-output-label")
                yield Input(id="bitwise-output-oct", disabled=True)

    def on_mount(self) -> None:
        self.query_one("#bitwise-error", Label).update("")
        self._update_visibility()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "bitwise-operation-select":
            self._update_visibility()

    def _update_visibility(self) -> None:
        operation = self.query_one("#bitwise-operation-select", Select).value
        input2 = self.query_one("#bitwise-input-2", Input)
        input2_label = self.query_one("#bitwise-input-2-label", Label)

        if operation in ["convert", "not"]:
            input2.display = False
            input2_label.display = False
        else:
            input2.display = True
            input2_label.display = True

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-bitwise-execute":
            self.execute_operation()

    def execute_operation(self) -> None:
        operation = self.query_one("#bitwise-operation-select", Select).value
        num1_str = self.query_one("#bitwise-input-1", Input).value.strip()
        num2_str = self.query_one("#bitwise-input-2", Input).value.strip()

        error_label = self.query_one("#bitwise-error", Label)
        dec_out = self.query_one("#bitwise-output-dec", Input)
        hex_out = self.query_one("#bitwise-output-hex", Input)
        bin_out = self.query_one("#bitwise-output-bin", Input)
        oct_out = self.query_one("#bitwise-output-oct", Input)

        error_label.update("")
        dec_out.value = ""
        hex_out.value = ""
        bin_out.value = ""
        oct_out.value = ""

        if not num1_str:
            error_label.update("Error: Number 1 is required.")
            return

        if operation not in ["convert", "not"] and not num2_str:
            error_label.update("Error: Number 2 is required for this operation.")
            return

        try:
            if operation == "convert":
                res = self.manager.format_number(self.manager.parse_number(num1_str))
            elif operation == "not":
                res = self.manager.bitwise_not(num1_str)
            elif operation == "and":
                res = self.manager.bitwise_and(num1_str, num2_str)
            elif operation == "or":
                res = self.manager.bitwise_or(num1_str, num2_str)
            elif operation == "xor":
                res = self.manager.bitwise_xor(num1_str, num2_str)
            elif operation == "lshift":
                res = self.manager.left_shift(num1_str, num2_str)
            elif operation == "rshift":
                res = self.manager.right_shift(num1_str, num2_str)
            else:
                error_label.update(f"Unknown operation: {operation}")
                return

            dec_out.value = res["dec"]
            hex_out.value = res["hex"]
            bin_out.value = res["bin"]
            oct_out.value = res["oct"]
        except ValueError as e:
            error_label.update(f"Error: {e}")
        except Exception as e:
            error_label.update(f"Unexpected error: {e}")
