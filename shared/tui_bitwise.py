from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, Select
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.bitwise_lab import BitwiseLabManager


class BitwiseLabTab(Container):
    """Tab for interactive Bitwise operations."""

    DEFAULT_CSS = """
    BitwiseLabTab {
        layout: vertical;
        height: 100%;
    }
    .bw-box {
        background: $boost;
        padding: 1;
        margin-bottom: 1;
    }
    .bit-row {
        height: 3;
        margin-bottom: 1;
    }
    .bit-btn {
        min-width: 4;
        margin-right: 1;
    }
    .op-row {
        height: auto;
        margin-top: 1;
        margin-bottom: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = BitwiseLabManager()
        self.current_value = 0
        self.bits_width = 32

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Bitwise Lab[/bold]", classes="welcome-text")

            with Vertical(classes="bw-box"):
                yield Label("Settings:")
                with Horizontal(classes="op-row"):
                    yield Select.from_values([8, 16, 32, 64], id="sel-bw-width", value=32)
                    yield Button("Clear (0)", id="btn-bw-clear", variant="error")
                    yield Button("Invert (~)", id="btn-bw-not", variant="warning")
                    yield Button("Swap Bytes", id="btn-bw-swap", variant="warning")
                    yield Button("Shift Left (<< 1)", id="btn-bw-lshift", variant="default")
                    yield Button("Shift Right (>> 1)", id="btn-bw-rshift", variant="default")

                yield Label("Enter Value (Dec/Hex/Oct/Bin):")
                with Horizontal(classes="op-row"):
                    yield Input(placeholder="e.g. 255, 0xFF, 0b1111", id="input-bw-val", value="0")
                    yield Button("Apply", id="btn-bw-apply", variant="primary")

                yield Label("[bold]Bit Editor (Click to toggle):[/bold]")
                # We will render the bits dynamically
                with Horizontal(id="container-bits", classes="bit-row"):
                    pass

                yield Label("[bold]Results[/bold]")
                yield RichLog(id="log-bw-results", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.update_bits_ui()
        self.update_results()

    @on(Select.Changed, "#sel-bw-width")
    def on_width_changed(self, event: Select.Changed) -> None:
        if event.value is not None:
            self.bits_width = int(event.value)
            mask = (1 << self.bits_width) - 1
            self.current_value &= mask
            self.update_bits_ui()
            self.update_results()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "btn-bw-apply":
            val_str = self.query_one("#input-bw-val", Input).value
            try:
                self.current_value = self.manager.parse_value(val_str)
                mask = (1 << self.bits_width) - 1
                self.current_value &= mask
                self.update_bits_ui()
                self.update_results()
            except ValueError as e:
                self.notify(f"Error parsing value: {e}", severity="error")
        elif btn_id == "btn-bw-clear":
            self.current_value = 0
            self.update_bits_ui()
            self.update_results()
            self.query_one("#input-bw-val", Input).value = "0"
        elif btn_id == "btn-bw-not":
            self.current_value = self.manager.bitwise_not(self.current_value, self.bits_width)
            self.update_bits_ui()
            self.update_results()
        elif btn_id == "btn-bw-swap":
            if self.bits_width in [16, 32, 64]:
                self.current_value = self.manager.swap_bytes(self.current_value, self.bits_width)
                self.update_bits_ui()
                self.update_results()
            else:
                self.notify("Byte swapping only supported for 16, 32, 64 bits.", severity="warning")
        elif btn_id == "btn-bw-lshift":
            self.current_value = self.manager.bitwise_lshift(self.current_value, 1, self.bits_width)
            self.update_bits_ui()
            self.update_results()
        elif btn_id == "btn-bw-rshift":
            self.current_value = self.manager.bitwise_rshift(self.current_value, 1, self.bits_width)
            self.update_bits_ui()
            self.update_results()
        elif btn_id and btn_id.startswith("bit-btn-"):
            # Toggle individual bit
            bit_idx = int(btn_id.replace("bit-btn-", ""))
            self.current_value ^= (1 << bit_idx)
            # Update the specific button visually to avoid full re-render
            is_set = bool(self.current_value & (1 << bit_idx))
            event.button.label = "1" if is_set else "0"
            event.button.variant = "primary" if is_set else "default"
            self.update_results()

    @on(Input.Submitted, "#input-bw-val")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.post_message(Button.Pressed(self.query_one("#btn-bw-apply", Button)))

    def update_bits_ui(self) -> None:
        container = self.query_one("#container-bits", Horizontal)
        # Remove existing bits
        for child in container.children:
            child.remove()

        # Re-create bits from MSB to LSB
        for i in range(self.bits_width - 1, -1, -1):
            is_set = bool(self.current_value & (1 << i))
            btn = Button(
                "1" if is_set else "0",
                id=f"bit-btn-{i}",
                variant="primary" if is_set else "default",
                classes="bit-btn"
            )
            container.mount(btn)

    def update_results(self) -> None:
        log = self.query_one("#log-bw-results", RichLog)
        log.clear()

        formatted = self.manager.format_value(self.current_value, self.bits_width)

        output = (
            f"[bold cyan]Decimal (Unsigned):[/bold cyan] {formatted['dec_unsigned']}\n"
            f"[bold cyan]Decimal (Signed):[/bold cyan]   {formatted['dec_signed']}\n"
            f"[bold green]Hexadecimal:[/bold green]        {formatted['hex']}\n"
            f"[bold yellow]Binary:[/bold yellow]             {formatted['bin']}\n"
            f"[bold magenta]Octal:[/bold magenta]              {formatted['oct']}\n"
        )
        log.write(output)
