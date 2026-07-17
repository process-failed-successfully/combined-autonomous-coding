from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Label, Input, Button, Markdown, DataTable
from textual import on
from shared.grok_lab import GrokManager

from textual.widgets import TabPane


class GrokLabTab(TabPane):
    """TUI tab for Grok pattern parsing."""

    def __init__(self, **kwargs):
        super().__init__("Grok Lab", id="tab-grok", **kwargs)
        self.manager = GrokManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("Grok Pattern:", classes="section-header")
            yield Input(placeholder="%{IPV4:clientip} %{WORD:verb}", id="grok-pattern")

            yield Label("Text to Parse:", classes="section-header")
            yield Input(placeholder="127.0.0.1 GET", id="grok-text")

            with Horizontal():
                yield Button("Parse", id="grok-parse-btn", variant="primary")
                yield Button("Show Patterns", id="grok-patterns-btn")

            yield Label("Result:", classes="section-header")
            yield Markdown("", id="grok-result")

            yield Label("Available Patterns", id="grok-patterns-header", classes="section-header")
            yield DataTable(id="grok-patterns-table")

    def on_mount(self) -> None:
        table = self.query_one("#grok-patterns-table", DataTable)
        table.add_columns("Name", "Pattern")
        table.display = False
        self.query_one("#grok-patterns-header").display = False

    @on(Button.Pressed, "#grok-parse-btn")
    def on_parse(self, event: Button.Pressed) -> None:
        pattern = self.query_one("#grok-pattern", Input).value
        text = self.query_one("#grok-text", Input).value
        result_md = self.query_one("#grok-result", Markdown)

        if not pattern or not text:
            result_md.update("Error: Pattern and text cannot be empty.")
            return

        try:
            parsed = self.manager.parse(pattern, text)
            if parsed:
                md = "```json\n"
                import json
                md += json.dumps(parsed, indent=2)
                md += "\n```"
                result_md.update(md)
            else:
                result_md.update("**No match found.**")
        except Exception as e:
            result_md.update(f"**Error:** {e}")

    @on(Button.Pressed, "#grok-patterns-btn")
    def on_show_patterns(self, event: Button.Pressed) -> None:
        table = self.query_one("#grok-patterns-table", DataTable)
        header = self.query_one("#grok-patterns-header")

        if table.display:
            table.display = False
            header.display = False
            return

        table.display = True
        header.display = True

        if table.row_count == 0:
            for name, patt in sorted(self.manager.list_patterns().items()):
                table.add_row(name, patt)
