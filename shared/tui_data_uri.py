from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Input, Button, RichLog, Select, Checkbox, TextArea, TabbedContent, TabPane
from textual import on
import urllib.parse
from shared.data_uri_lab import DataUriLabManager

class DataUriLabTab(Container):
    """Tab for Data URI Lab."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = DataUriLabManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]Data URI Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                with TabPane("Encode Text/File"):
                    with Vertical(classes="stat-box"):
                        yield Label("Encode to Data URI")

                        with TabbedContent(id="encode-tabs"):
                            with TabPane("Text", id="tab-encode-text"):
                                yield Label("Text to encode:")
                                yield TextArea(id="encode-text-input")
                                yield Checkbox("Use Base64 Encoding", id="encode-use-base64", value=True)

                            with TabPane("File", id="tab-encode-file"):
                                yield Label("File path:")
                                yield Input(placeholder="/path/to/file.png", id="encode-file-input")

                        yield Label("MIME Type (optional, e.g. image/png, text/plain):")
                        yield Input(placeholder="auto-detect or text/plain", id="encode-mime-input")

                        yield Button("Generate Data URI", id="btn-generate-uri", variant="primary")

                        yield Label("Generated URI:")
                        yield RichLog(id="encode-output-log", wrap=True, highlight=True)

                with TabPane("Decode URI"):
                    with Vertical(classes="stat-box"):
                        yield Label("Decode Data URI")
                        yield Label("Data URI:")
                        yield TextArea(id="decode-uri-input")

                        with Horizontal():
                            yield Button("Decode & View Data", id="btn-decode-uri", variant="success")
                            yield Button("Show Info Only", id="btn-decode-info", variant="primary")

                        yield Label("Output File (optional, to save binary data):")
                        yield Input(placeholder="/path/to/save/output.bin", id="decode-output-file")

                        yield Label("Result:")
                        yield RichLog(id="decode-output-log", wrap=True, highlight=True)

    @on(Button.Pressed, "#btn-generate-uri")
    def on_generate_uri(self) -> None:
        active_tab = self.query_one("#encode-tabs", TabbedContent).active
        mime = self.query_one("#encode-mime-input", Input).value
        log = self.query_one("#encode-output-log", RichLog)

        try:
            if active_tab == "tab-encode-text":
                text = self.query_one("#encode-text-input", TextArea).text
                if not text:
                    self.notify("Please enter text to encode.", severity="warning")
                    return
                use_base64 = self.query_one("#encode-use-base64", Checkbox).value
                mime_type = mime or "text/plain"
                result = self.manager.encode_text(text, mime_type, use_base64)

            elif active_tab == "tab-encode-file":
                filepath = self.query_one("#encode-file-input", Input).value
                if not filepath:
                    self.notify("Please enter a file path.", severity="warning")
                    return
                result = self.manager.encode_file(filepath, mime if mime else None)

            log.clear()
            log.write(result)
            self.notify("Data URI generated.")

        except Exception as e:
            log.clear()
            log.write(f"[red]Error:[/red] {str(e)}")
            self.notify("Failed to generate Data URI.", severity="error")

    @on(Button.Pressed, "#btn-decode-uri")
    def on_decode_uri(self) -> None:
        self._perform_decode(show_data=True)

    @on(Button.Pressed, "#btn-decode-info")
    def on_decode_info(self) -> None:
        self._perform_decode(show_data=False)

    def _perform_decode(self, show_data: bool) -> None:
        uri = self.query_one("#decode-uri-input", TextArea).text.strip()
        out_file = self.query_one("#decode-output-file", Input).value
        log = self.query_one("#decode-output-log", RichLog)

        if not uri:
            self.notify("Please enter a Data URI to decode.", severity="warning")
            return

        try:
            result = self.manager.decode(uri)

            log.clear()
            log.write(f"[bold]MIME Type:[/bold] {result['mime_type']}")
            log.write(f"[bold]Base64 Encoded:[/bold] {result['is_base64']}")
            log.write(f"[bold]Data Length:[/bold] {len(result['data'])} bytes")

            if show_data:
                if out_file:
                    with open(out_file, "wb") as f:
                        f.write(result['data'])
                    log.write(f"\n[green]✅ Data saved to {out_file}[/green]")
                    self.notify(f"Saved to {out_file}")
                else:
                    log.write("\n[bold]Data Preview:[/bold]")
                    try:
                        # Try decoding as string
                        text = result['data'].decode('utf-8')
                        log.write(text)
                    except UnicodeDecodeError:
                        log.write("[yellow]Data appears to be binary. Showing hex dump preview...[/yellow]")
                        log.write(result['data'][:200].hex())
                        if len(result['data']) > 200:
                            log.write("...")
                        log.write("[dim]Provide an Output File path to save the full binary data.[/dim]")

        except Exception as e:
            log.clear()
            log.write(f"[red]Error:[/red] {str(e)}")
            self.notify("Failed to decode Data URI.", severity="error")
