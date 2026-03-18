from pathlib import Path
import json
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Input, TextArea, RichLog
from textual import on

from shared.vcard_lab import VCardManager

class VCardTab(Container):
    """Tab for generating and parsing vCards."""

    def __init__(self, project_dir: Path = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = VCardManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]vCard Lab[/bold]", classes="welcome-text")

            with Horizontal():
                # Left Pane: Generate vCard
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Generate vCard[/bold]")
                    yield Input(placeholder="Full Name (FN)", id="vcard-fn")
                    yield Input(placeholder="Name (N) (Last;First;Middle;Prefix;Suffix)", id="vcard-n")
                    yield Input(placeholder="Organization (ORG)", id="vcard-org")
                    yield Input(placeholder="Title (TITLE)", id="vcard-title")
                    yield Input(placeholder="Email (EMAIL)", id="vcard-email")
                    yield Input(placeholder="Phone (TEL)", id="vcard-tel")
                    yield Input(placeholder="URL", id="vcard-url")
                    yield Input(placeholder="Address (ADR)", id="vcard-adr")
                    yield Input(placeholder="Note (NOTE)", id="vcard-note")

                    yield Button("Generate", id="btn-vcard-generate", variant="primary")
                    yield RichLog(id="vcard-gen-output", wrap=True, highlight=True, markup=True)

                # Right Pane: Parse vCard
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Parse vCard[/bold]")
                    yield TextArea(id="vcard-parse-input")
                    yield Button("Parse", id="btn-vcard-parse", variant="warning")
                    yield RichLog(id="vcard-parse-output", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-vcard-generate")
    def on_generate(self) -> None:
        details = {}

        # Helper to get value and add to details if not empty
        def add_detail(key, input_id):
            val = self.query_one(f"#{input_id}", Input).value.strip()
            if val:
                details[key] = val

        add_detail("fn", "vcard-fn")
        add_detail("n", "vcard-n")
        add_detail("org", "vcard-org")
        add_detail("title", "vcard-title")
        add_detail("email", "vcard-email")
        add_detail("tel", "vcard-tel")
        add_detail("url", "vcard-url")
        add_detail("adr", "vcard-adr")
        add_detail("note", "vcard-note")

        log = self.query_one("#vcard-gen-output", RichLog)
        log.clear()

        if not details:
            log.write("[red]Error: Provide at least one detail to generate vCard.[/red]")
            return

        vcard_str = self.manager.generate_vcard(details)
        log.write(vcard_str)

    @on(Button.Pressed, "#btn-vcard-parse")
    def on_parse(self) -> None:
        content = self.query_one("#vcard-parse-input", TextArea).text
        log = self.query_one("#vcard-parse-output", RichLog)
        log.clear()

        if not content.strip():
            log.write("[red]Error: Paste vCard content to parse.[/red]")
            return

        try:
            vcards = self.manager.parse_vcard(content)
            if not vcards:
                log.write("No vCards found.")
            else:
                log.write(json.dumps(vcards, indent=2))
        except Exception as e:
            log.write(f"[red]Error parsing vCard: {e}[/red]")
