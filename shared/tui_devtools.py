import hashlib
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, RichLog, TextArea, Select, TabbedContent, TabPane
from textual import on
from shared.devtools import DevTools

class DevToolsTab(Container):
    """Tab for developer utilities."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Developer Tools[/bold]", classes="welcome-text")

            with TabbedContent():
                # --- Epoch Converter ---
                with TabPane("Epoch"):
                    with Vertical(classes="stat-box"):
                        yield Label("Timestamp to Date")
                        with Horizontal():
                            yield Input(placeholder="Epoch Timestamp...", id="dt-epoch-input")
                            yield Button("Convert", id="btn-epoch-to-date", variant="primary")
                        yield Label("", id="dt-epoch-result")

                        yield Label("\nDate to Timestamp")
                        with Horizontal():
                            yield Input(placeholder="YYYY-MM-DD HH:MM:SS", id="dt-date-input")
                            yield Button("Convert", id="btn-date-to-epoch", variant="primary")
                        yield Label("", id="dt-date-result")

                # --- Base64 ---
                with TabPane("Base64"):
                    with Vertical(classes="stat-box"):
                        yield Label("Input Text")
                        yield TextArea(id="dt-b64-input", show_line_numbers=False)
                        with Horizontal():
                            yield Button("Encode", id="btn-b64-encode", variant="primary")
                            yield Button("Decode", id="btn-b64-decode", variant="warning")
                        yield Label("Output")
                        yield TextArea(id="dt-b64-output", read_only=True, show_line_numbers=False)

                # --- UUID ---
                with TabPane("UUID"):
                    with Vertical(classes="stat-box"):
                        yield Button("Generate UUID", id="btn-uuid-gen", variant="success")
                        yield RichLog(id="dt-uuid-log", markup=True)

                # --- Hash ---
                with TabPane("Hash"):
                    with Vertical(classes="stat-box"):
                        yield Label("Input Text")
                        yield TextArea(id="dt-hash-input", show_line_numbers=False)
                        with Horizontal():
                            yield Select.from_values(list(hashlib.algorithms_available), id="dt-hash-algo", value="sha256")
                            yield Button("Calculate Hash", id="btn-hash-calc", variant="primary")
                        yield Label("Output Hash")
                        yield Input(disabled=True, id="dt-hash-output")

                # --- JSON ---
                with TabPane("JSON"):
                    with Vertical(classes="stat-box"):
                        yield Label("Input JSON")
                        yield TextArea(id="dt-json-input", language="json")
                        yield Button("Format / Validate", id="btn-json-fmt", variant="success")
                        yield Label("Output JSON")
                        yield TextArea(id="dt-json-output", language="json", read_only=True)

    @on(Button.Pressed, "#btn-epoch-to-date")
    def on_epoch_to_date(self):
        val = self.query_one("#dt-epoch-input", Input).value
        try:
            ts = float(val)
            res = DevTools.epoch_to_date(ts)
            self.query_one("#dt-epoch-result", Label).update(f"[green]{res}[/green]")
        except ValueError:
            self.query_one("#dt-epoch-result", Label).update("[red]Invalid timestamp[/red]")

    @on(Button.Pressed, "#btn-date-to-epoch")
    def on_date_to_epoch(self):
        val = self.query_one("#dt-date-input", Input).value
        try:
            ts = DevTools.date_to_epoch(val)
            self.query_one("#dt-date-result", Label).update(f"[green]{ts}[/green]")
        except ValueError:
            self.query_one("#dt-date-result", Label).update("[red]Invalid date format (try YYYY-MM-DD HH:MM:SS)[/red]")

    @on(Button.Pressed, "#btn-b64-encode")
    def on_b64_encode(self):
        text = self.query_one("#dt-b64-input", TextArea).text
        res = DevTools.base64_encode(text)
        self.query_one("#dt-b64-output", TextArea).text = res

    @on(Button.Pressed, "#btn-b64-decode")
    def on_b64_decode(self):
        text = self.query_one("#dt-b64-input", TextArea).text
        res = DevTools.base64_decode(text)
        self.query_one("#dt-b64-output", TextArea).text = res

    @on(Button.Pressed, "#btn-uuid-gen")
    def on_uuid_gen(self):
        uid = DevTools.generate_uuid()
        self.query_one("#dt-uuid-log", RichLog).write(f"[bold green]{uid}[/bold green]")

    @on(Button.Pressed, "#btn-hash-calc")
    def on_hash_calc(self):
        text = self.query_one("#dt-hash-input", TextArea).text
        algo = self.query_one("#dt-hash-algo", Select).value
        res = DevTools.calculate_hash(text, algo)
        self.query_one("#dt-hash-output", Input).value = res

    @on(Button.Pressed, "#btn-json-fmt")
    def on_json_fmt(self):
        text = self.query_one("#dt-json-input", TextArea).text
        res = DevTools.format_json(text)
        self.query_one("#dt-json-output", TextArea).text = res
