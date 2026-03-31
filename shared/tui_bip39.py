from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Button,
    Input,
    Static,
    Select,
    Label,
    TextArea,
    Log
)

from shared.bip39_lab import Bip39LabManager, HAS_MNEMONIC


class Bip39LabTab(Vertical):
    """TUI Tab for BIP39 operations."""

    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir
        self.manager = Bip39LabManager() if HAS_MNEMONIC else None

    def compose(self) -> ComposeResult:
        if not HAS_MNEMONIC:
            yield Static("Error: mnemonic library is not installed.", id="bip39-error")
            return

        with Vertical(classes="bip39-container"):
            yield Static("BIP39 Mnemonic and Seed Generator", classes="header")

            with Horizontal(classes="bip39-controls"):
                yield Label("Word Count:")
                yield Select(
                    [("12 Words (128 bit)", 128),
                     ("15 Words (160 bit)", 160),
                     ("18 Words (192 bit)", 192),
                     ("21 Words (224 bit)", 224),
                     ("24 Words (256 bit)", 256)],
                    id="bip39-strength",
                    value=128
                )
                yield Button("Generate", id="btn-bip39-generate", variant="primary")

            with Vertical(classes="bip39-inputs"):
                yield Label("Mnemonic Phrase:")
                yield Input(id="bip39-phrase", placeholder="Enter or generate a BIP39 mnemonic phrase...")
                yield Label("Passphrase (Optional):")
                yield Input(id="bip39-passphrase", placeholder="Optional passphrase for seed generation...", password=False)

            with Horizontal(classes="bip39-actions"):
                yield Button("Validate Phrase", id="btn-bip39-validate", variant="warning")
                yield Button("Generate Seed", id="btn-bip39-seed", variant="success")

            with Vertical(classes="bip39-output"):
                yield Label("Hex Seed Output:")
                yield TextArea(id="bip39-seed-output", language="text", read_only=True)

            with Vertical(classes="bip39-logs"):
                yield Label("Logs:")
                yield Log(id="bip39-log")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log_widget = self.query_one("#bip39-log", Log)
        phrase_input = self.query_one("#bip39-phrase", Input)
        passphrase_input = self.query_one("#bip39-passphrase", Input)
        seed_output = self.query_one("#bip39-seed-output", TextArea)
        strength_select = self.query_one("#bip39-strength", Select)

        if not self.manager:
            log_widget.write_line("Error: BIP39 manager not initialized.")
            return

        if event.button.id == "btn-bip39-generate":
            try:
                strength = strength_select.value
                phrase = self.manager.generate(strength=strength)
                phrase_input.value = phrase
                log_widget.write_line(f"Generated {strength}-bit mnemonic phrase.")
                seed_output.text = ""
            except Exception as e:
                log_widget.write_line(f"Error generating phrase: {e}")

        elif event.button.id == "btn-bip39-validate":
            phrase = phrase_input.value.strip()
            if not phrase:
                log_widget.write_line("Error: Phrase is empty.")
                return
            try:
                is_valid = self.manager.validate(phrase)
                if is_valid:
                    log_widget.write_line("✅ Phrase is a valid BIP39 mnemonic.")
                else:
                    log_widget.write_line("❌ Phrase is invalid.")
            except Exception as e:
                log_widget.write_line(f"Error validating phrase: {e}")

        elif event.button.id == "btn-bip39-seed":
            phrase = phrase_input.value.strip()
            passphrase = passphrase_input.value
            if not phrase:
                log_widget.write_line("Error: Phrase is empty.")
                return
            try:
                seed = self.manager.generate_seed(phrase, passphrase=passphrase)
                seed_hex = seed.hex()
                seed_output.text = seed_hex
                log_widget.write_line("✅ Seed generated successfully.")
            except Exception as e:
                log_widget.write_line(f"❌ Error generating seed: {e}")
                seed_output.text = ""
