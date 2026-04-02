from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, TextArea, Static, Input, Select
from textual.reactive import reactive
from textual.binding import Binding

from shared.bip39_lab import Bip39LabManager


class Bip39Tab(Container):
    """A Textual tab for BIP39 mnemonic phrase operations."""

    BINDINGS = [
        Binding("ctrl+r", "execute", "Execute"),
        Binding("ctrl+x", "clear", "Clear Inputs"),
    ]

    mode: reactive[str] = reactive("generate")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.manager = Bip39LabManager()
        except Exception as e:
            self.manager = None
            self.init_error = str(e)

    def compose(self) -> ComposeResult:
        if not hasattr(self, 'manager') or self.manager is None:
            yield Static(f"Error loading BIP39 Lab: {getattr(self, 'init_error', 'Unknown Error')}", id="bip39-error")
            return

        with Horizontal(id="bip39-controls", classes="toolbar"):
            yield Select(
                [
                    ("Generate", "generate"),
                    ("Validate", "validate"),
                    ("To Seed", "seed"),
                ],
                value=self.mode,
                id="bip39-mode-select"
            )
            yield Button("Execute", id="bip39-btn-execute", variant="primary")
            yield Button("Clear", id="bip39-btn-clear", variant="warning")

        # Dynamic options area based on mode
        with Vertical(id="bip39-options-area"):
            # Generate Options
            with Horizontal(id="bip39-gen-options", classes="bip39-option-row"):
                yield Static("Strength (bits): ", classes="label")
                yield Select(
                    [
                        ("128 (12 words)", 128),
                        ("160 (15 words)", 160),
                        ("192 (18 words)", 192),
                        ("224 (21 words)", 224),
                        ("256 (24 words)", 256),
                    ],
                    value=128,
                    id="bip39-strength-select"
                )

            # Seed Options
            with Horizontal(id="bip39-seed-options", classes="bip39-option-row"):
                yield Static("Passphrase: ", classes="label")
                yield Input(placeholder="Optional passphrase", id="bip39-passphrase-input", password=True)

        with Horizontal(id="bip39-io-area"):
            with Vertical(classes="bip39-pane"):
                yield Static("Input (Mnemonic Phrase):", classes="pane-header")
                yield TextArea(id="bip39-input")

            with Vertical(classes="bip39-pane"):
                yield Static("Output:", classes="pane-header")
                yield TextArea(id="bip39-output", read_only=True)

    def on_mount(self) -> None:
        self.update_ui_for_mode()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "bip39-mode-select":
            self.mode = str(event.value)
            self.update_ui_for_mode()

    def update_ui_for_mode(self) -> None:
        try:
            gen_options = self.query_one("#bip39-gen-options", Horizontal)
            seed_options = self.query_one("#bip39-seed-options", Horizontal)
            input_area = self.query_one("#bip39-input", TextArea)

            if self.mode == "generate":
                gen_options.display = True
                seed_options.display = False
                input_area.disabled = True
            elif self.mode == "validate":
                gen_options.display = False
                seed_options.display = False
                input_area.disabled = False
            elif self.mode == "seed":
                gen_options.display = False
                seed_options.display = True
                input_area.disabled = False
        except Exception:
            pass  # Ignore if not mounted yet

    def action_execute(self) -> None:
        self.execute_operation()

    def action_clear(self) -> None:
        self.clear_inputs()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "bip39-btn-execute":
            self.execute_operation()
        elif event.button.id == "bip39-btn-clear":
            self.clear_inputs()

    def clear_inputs(self) -> None:
        try:
            self.query_one("#bip39-input", TextArea).text = ""
            self.query_one("#bip39-output", TextArea).text = ""
            self.query_one("#bip39-passphrase-input", Input).value = ""
        except Exception:
            pass

    def execute_operation(self) -> None:
        if not hasattr(self, 'manager') or self.manager is None:
            return

        try:
            output_area = self.query_one("#bip39-output", TextArea)
            input_text = self.query_one("#bip39-input", TextArea).text.strip()

            if self.mode == "generate":
                strength = self.query_one("#bip39-strength-select", Select).value
                result = self.manager.generate(strength=int(strength) if strength else 128)
                if result["success"]:
                    output_area.text = result["phrase"]
                else:
                    output_area.text = f"Error: {result['error']}"

            elif self.mode == "validate":
                if not input_text:
                    output_area.text = "Error: Input phrase is empty."
                    return
                result = self.manager.validate(input_text)
                if result["success"]:
                    output_area.text = f"Valid: {result['valid']}"
                else:
                    output_area.text = f"Error: {result['error']}"

            elif self.mode == "seed":
                if not input_text:
                    output_area.text = "Error: Input phrase is empty."
                    return
                passphrase = self.query_one("#bip39-passphrase-input", Input).value
                result = self.manager.to_seed(input_text, passphrase=passphrase)

                if result["success"]:
                    text = f"Seed (Hex):\n{result['seed_hex']}"
                    if not result["valid_phrase"]:
                        text = "WARNING: The mnemonic phrase provided is invalid.\n\n" + text
                    output_area.text = text
                else:
                    output_area.text = f"Error: {result['error']}"

        except Exception as e:
            try:
                self.query_one("#bip39-output", TextArea).text = f"Exception: {str(e)}"
            except Exception:
                pass
