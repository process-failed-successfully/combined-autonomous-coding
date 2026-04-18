from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Label, Button, Input, Checkbox, TextArea, RichLog
from textual.containers import Container
from textual.widgets import TabPane

from shared.mask_lab import MaskLabManager

class MaskLabTab(TabPane):
    """Tab for experimenting with PII Data Masking."""

    def __init__(self):
        super().__init__("Mask Lab", id="tab-mask")
        self.manager = MaskLabManager()

    def compose(self) -> ComposeResult:
        yield Label("[bold]PII Data Masking Lab[/bold]", classes="welcome-text")

        with Horizontal():
            with VerticalScroll(classes="w-1-2", id="mask-left-col"):
                yield Label("Input Text:")
                yield TextArea(id="mask-input", language="markdown")

                yield Label("Select PII to Mask:")
                with Horizontal(id="mask-options"):
                    yield Checkbox("Email", id="mask-chk-email", value=True)
                    yield Checkbox("Phone", id="mask-chk-phone", value=True)
                    yield Checkbox("Credit Card", id="mask-chk-credit_card", value=True)
                    yield Checkbox("SSN", id="mask-chk-ssn", value=True)
                    yield Checkbox("IPv4", id="mask-chk-ipv4", value=True)

                yield Label("Mask Character:")
                yield Input(value="*", id="mask-char", placeholder="*")

                yield Button("Mask Data", id="btn-mask-data", variant="primary")

            with VerticalScroll(classes="w-1-2 stat-box", id="mask-right-col"):
                yield Label("Masked Output:")
                yield TextArea(id="mask-output", read_only=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-mask-data":
            self.mask_data()

    def mask_data(self) -> None:
        text = self.query_one("#mask-input", TextArea).text
        if not text:
            self.notify("Please enter some text to mask.", severity="warning")
            return

        rules = []
        if self.query_one("#mask-chk-email", Checkbox).value:
            rules.append("email")
        if self.query_one("#mask-chk-phone", Checkbox).value:
            rules.append("phone")
        if self.query_one("#mask-chk-credit_card", Checkbox).value:
            rules.append("credit_card")
        if self.query_one("#mask-chk-ssn", Checkbox).value:
            rules.append("ssn")
        if self.query_one("#mask-chk-ipv4", Checkbox).value:
            rules.append("ipv4")

        mask_char = self.query_one("#mask-char", Input).value or "*"

        masked_text = self.manager.mask_text(text, rules=rules, mask_char=mask_char)

        output_area = self.query_one("#mask-output", TextArea)
        output_area.text = masked_text
        self.notify("Data masked successfully.", severity="success")
