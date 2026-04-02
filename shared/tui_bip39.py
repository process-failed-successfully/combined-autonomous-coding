from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Label, Button, TextArea, Input, Select
from shared.bip39_lab import Bip39LabManager

class Bip39LabTab(ScrollableContainer):
    """TUI Tab for BIP39 Lab."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = Bip39LabManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="tab-content"):
            yield Label("[bold]BIP39 Lab[/bold] - Generate, Validate, and Convert Mnemonics", classes="tab-title")

            with Horizontal(classes="action-bar"):
                yield Select.from_values([12, 15, 18, 21, 24], id="bip39-words-select", value=12)
                yield Button("Generate", id="btn-bip39-generate", variant="primary")
                yield Button("Validate", id="btn-bip39-validate", variant="warning")
                yield Button("To Seed", id="btn-bip39-seed", variant="success")
                yield Button("Clear", id="btn-bip39-clear", variant="error")

            with Horizontal():
                with Vertical(classes="panel"):
                    yield Label("Mnemonic Phrase:")
                    yield TextArea(id="bip39-phrase-area", language="text")

                with Vertical(classes="panel"):
                    yield Label("Passphrase (Optional for Seed):")
                    yield Input(placeholder="Passphrase...", id="bip39-passphrase-input", password=True)
                    yield Label("Output:")
                    yield TextArea(id="bip39-output-area", language="text", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-bip39-generate":
            self.generate_phrase()
        elif event.button.id == "btn-bip39-validate":
            self.validate_phrase()
        elif event.button.id == "btn-bip39-seed":
            self.convert_to_seed()
        elif event.button.id == "btn-bip39-clear":
            self.clear_all()

    def generate_phrase(self) -> None:
        words_select = self.query_one("#bip39-words-select", Select)
        words = int(words_select.value) if words_select.value else 12

        result = self.manager.generate(words=words)
        output_area = self.query_one("#bip39-output-area", TextArea)

        if result["success"]:
            self.query_one("#bip39-phrase-area", TextArea).text = result["phrase"]
            output_area.text = "Mnemonic generated successfully."
            self.app.notify("Mnemonic generated.")
        else:
            output_area.text = f"Error: {result['error']}"
            self.app.notify("Generation failed.", severity="error")

    def validate_phrase(self) -> None:
        phrase = self.query_one("#bip39-phrase-area", TextArea).text.strip()
        output_area = self.query_one("#bip39-output-area", TextArea)

        if not phrase:
            output_area.text = "Please provide a mnemonic phrase to validate."
            self.app.notify("Mnemonic required.", severity="error")
            return

        result = self.manager.validate(phrase)

        if result["success"]:
            if result["is_valid"]:
                output_area.text = "The mnemonic phrase is VALID."
                self.app.notify("Valid mnemonic.")
            else:
                output_area.text = "The mnemonic phrase is INVALID."
                self.app.notify("Invalid mnemonic.", severity="warning")
        else:
            output_area.text = f"Error: {result['error']}"
            self.app.notify("Validation error.", severity="error")

    def convert_to_seed(self) -> None:
        phrase = self.query_one("#bip39-phrase-area", TextArea).text.strip()
        passphrase = self.query_one("#bip39-passphrase-input", Input).value
        output_area = self.query_one("#bip39-output-area", TextArea)

        if not phrase:
            output_area.text = "Please provide a mnemonic phrase to convert."
            self.app.notify("Mnemonic required.", severity="error")
            return

        result = self.manager.to_seed(phrase, passphrase)

        if result["success"]:
            output_area.text = f"Seed (Hex):\n{result['seed_hex']}"
            self.app.notify("Converted to seed.")
        else:
            output_area.text = f"Error: {result['error']}"
            self.app.notify("Conversion failed.", severity="error")

    def clear_all(self) -> None:
        self.query_one("#bip39-phrase-area", TextArea).text = ""
        self.query_one("#bip39-passphrase-input", Input).value = ""
        self.query_one("#bip39-output-area", TextArea).text = ""
        self.app.notify("Fields cleared.")