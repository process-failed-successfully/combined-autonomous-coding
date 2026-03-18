"""
Textual UI for the VCard Lab.
"""
import json
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Input, Button, TextArea, Static, Label
from shared.vcard_lab import VCardManager

class VCardLabTab(Container):
    """Tab for VCard operations."""

    def __init__(self, project_dir: Path | None = None):
        super().__init__(id="tab-vcard")
        self.project_dir = project_dir
        self.manager = VCardManager()

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="panel"):
                yield Label("Generate vCard", classes="panel-title")
                yield Input(placeholder="First Name", id="vcard-in-first")
                yield Input(placeholder="Last Name", id="vcard-in-last")
                yield Input(placeholder="Email", id="vcard-in-email")
                yield Input(placeholder="Phone", id="vcard-in-phone")
                yield Input(placeholder="Organization", id="vcard-in-org")
                yield Input(placeholder="Title", id="vcard-in-title")
                yield Input(placeholder="URL", id="vcard-in-url")
                yield Button("Generate", id="btn-vcard-generate", variant="primary")
                yield Static("", id="vcard-generate-error", classes="error-text")
                yield TextArea(id="vcard-out-generate", read_only=True, language="text", classes="output-area")

            with Vertical(classes="panel"):
                yield Label("Parse vCard", classes="panel-title")
                yield TextArea(id="vcard-in-parse", language="text", classes="input-area")
                yield Button("Parse", id="btn-vcard-parse", variant="primary")
                yield Static("", id="vcard-parse-error", classes="error-text")
                yield TextArea(id="vcard-out-parse", read_only=True, language="json", classes="output-area")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn-vcard-generate":
            await self._handle_generate()
        elif button_id == "btn-vcard-parse":
            await self._handle_parse()

    async def _handle_generate(self) -> None:
        first_input = self.query_one("#vcard-in-first", Input)
        last_input = self.query_one("#vcard-in-last", Input)
        email_input = self.query_one("#vcard-in-email", Input)
        phone_input = self.query_one("#vcard-in-phone", Input)
        org_input = self.query_one("#vcard-in-org", Input)
        title_input = self.query_one("#vcard-in-title", Input)
        url_input = self.query_one("#vcard-in-url", Input)

        out_area = self.query_one("#vcard-out-generate", TextArea)
        error_static = self.query_one("#vcard-generate-error", Static)

        first_name = first_input.value.strip()
        last_name = last_input.value.strip()

        if not first_name and not last_name:
            error_static.update("Error: Provide First Name or Last Name.")
            out_area.text = ""
            return

        error_static.update("")

        try:
            result = self.manager.generate(
                first_name=first_name,
                last_name=last_name,
                email=email_input.value.strip(),
                phone=phone_input.value.strip(),
                org=org_input.value.strip(),
                title=title_input.value.strip(),
                url=url_input.value.strip()
            )
            out_area.text = result
        except Exception as e:
            error_static.update(f"Error: {e}")
            out_area.text = ""

    async def _handle_parse(self) -> None:
        in_area = self.query_one("#vcard-in-parse", TextArea)
        out_area = self.query_one("#vcard-out-parse", TextArea)
        error_static = self.query_one("#vcard-parse-error", Static)

        vcard_text = in_area.text.strip()
        if not vcard_text:
            error_static.update("Error: Provide vCard text.")
            out_area.text = ""
            return

        error_static.update("")

        try:
            parsed = self.manager.parse(vcard_text)
            out_area.text = json.dumps(parsed, indent=2)
        except Exception as e:
            error_static.update(f"Error: {e}")
            out_area.text = ""
