from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Label, RichLog, TabbedContent, TabPane
import json

from shared.url_lab import UrlLabManager


class UrlLabTab(Container):
    """Tab for URL manipulation (Parse, Encode, Params, Normalize)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = UrlLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]URL Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                with TabPane("Parse", id="url-tab-parse"):
                    with Vertical(classes="stat-box"):
                        yield Label("Enter URL to Parse:")
                        yield Input(placeholder="https://example.com/path?query=1", id="url-parse-input")
                        yield Button("Parse URL", id="btn-url-parse", variant="primary")

                    yield Label("[bold]Parsed Output (JSON)[/bold]")
                    yield RichLog(id="url-parse-log", wrap=True, highlight=True, markup=True)

                with TabPane("Encode/Decode", id="url-tab-enc"):
                    with Vertical(classes="stat-box"):
                        yield Label("Enter Text:")
                        yield Input(placeholder="Text to encode/decode...", id="url-enc-input")

                        with Horizontal():
                            yield Button("Encode", id="btn-url-encode", variant="warning")
                            yield Button("Decode", id="btn-url-decode", variant="success")

                    yield Label("[bold]Result[/bold]")
                    yield RichLog(id="url-enc-log", wrap=True, highlight=True, markup=True)

                with TabPane("Params", id="url-tab-params"):
                    with Vertical(classes="stat-box"):
                        yield Label("Base URL:")
                        yield Input(placeholder="https://example.com", id="url-params-base")

                        yield Label("Manage Query Parameters:")
                        with Horizontal():
                            yield Input(placeholder="Key", id="url-param-key")
                            yield Input(placeholder="Value", id="url-param-val")
                            yield Button("Add/Set", id="btn-url-param-add", variant="primary")
                            yield Button("Remove Key", id="btn-url-param-remove", variant="error")

                    yield Label("[bold]Current Parameters[/bold]")
                    yield DataTable(id="url-params-table")

                    yield Label("[bold]Resulting URL[/bold]")
                    yield RichLog(id="url-params-result", wrap=True, highlight=True, markup=True)

                with TabPane("Normalize", id="url-tab-norm"):
                    with Vertical(classes="stat-box"):
                        yield Label("Enter URL to Normalize:")
                        yield Input(placeholder="HTTPS://EXAMPLE.COM:443/foo?b=2&a=1", id="url-norm-input")
                        yield Button("Normalize URL", id="btn-url-norm", variant="primary")

                    yield Label("[bold]Normalized URL[/bold]")
                    yield RichLog(id="url-norm-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#url-params-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Key", "Value")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-url-parse":
            self.action_parse()
        elif event.button.id == "btn-url-encode":
            self.action_encode()
        elif event.button.id == "btn-url-decode":
            self.action_decode()
        elif event.button.id == "btn-url-param-add":
            self.action_param_add()
        elif event.button.id == "btn-url-param-remove":
            self.action_param_remove()
        elif event.button.id == "btn-url-norm":
            self.action_normalize()

    def action_parse(self) -> None:
        url = self.query_one("#url-parse-input", Input).value
        log = self.query_one("#url-parse-log", RichLog)
        log.clear()

        if not url:
            log.write("[red]Please enter a URL.[/red]")
            return

        try:
            result = self.manager.parse(url)
            log.write(json.dumps(result, indent=2))
        except Exception as e:
            log.write(f"[red]Error parsing URL: {e}[/red]")

    def action_encode(self) -> None:
        text = self.query_one("#url-enc-input", Input).value
        log = self.query_one("#url-enc-log", RichLog)
        log.clear()

        if not text:
            log.write("[red]Please enter text.[/red]")
            return

        try:
            result = self.manager.encode(text)
            log.write(result)
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

    def action_decode(self) -> None:
        text = self.query_one("#url-enc-input", Input).value
        log = self.query_one("#url-enc-log", RichLog)
        log.clear()

        if not text:
            log.write("[red]Please enter text.[/red]")
            return

        try:
            result = self.manager.decode(text)
            log.write(result)
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")

    def action_param_add(self) -> None:
        url = self.query_one("#url-params-base", Input).value
        key = self.query_one("#url-param-key", Input).value
        val = self.query_one("#url-param-val", Input).value
        log = self.query_one("#url-params-result", RichLog)

        if not url:
            log.clear()
            log.write("[red]Base URL required.[/red]")
            return

        if not key or not val:
            log.clear()
            log.write("[red]Key and Value required.[/red]")
            return

        try:
            # Mode "add" appends, "set" overwrites. Let's use "add" based on button label.
            # The manager supports "add" and "set".
            new_url = self.manager.params(url, "add", key, val)

            # Update Input with new URL so subsequent adds work on the new state
            self.query_one("#url-params-base", Input).value = new_url

            # Clear inputs
            self.query_one("#url-param-key", Input).value = ""
            self.query_one("#url-param-val", Input).value = ""

            self.refresh_params_table(new_url)
            log.clear()
            log.write(new_url)

        except Exception as e:
            log.clear()
            log.write(f"[red]Error: {e}[/red]")

    def action_param_remove(self) -> None:
        url = self.query_one("#url-params-base", Input).value
        key = self.query_one("#url-param-key", Input).value
        log = self.query_one("#url-params-result", RichLog)

        if not url:
            log.clear()
            log.write("[red]Base URL required.[/red]")
            return

        if not key:
            log.clear()
            log.write("[red]Key required to remove.[/red]")
            return

        try:
            new_url = self.manager.params(url, "remove", key)
            self.query_one("#url-params-base", Input).value = new_url
            self.query_one("#url-param-key", Input).value = ""

            self.refresh_params_table(new_url)
            log.clear()
            log.write(new_url)
        except Exception as e:
            log.clear()
            log.write(f"[red]Error: {e}[/red]")

    def refresh_params_table(self, url: str) -> None:
        table = self.query_one("#url-params-table", DataTable)
        table.clear()

        try:
            parsed = self.manager.parse(url)
            params = parsed.get("query_params", {})

            for k, v_list in params.items():
                # v_list is a list of strings
                for v in v_list:
                    table.add_row(k, v)
        except Exception:
            pass

    def action_normalize(self) -> None:
        url = self.query_one("#url-norm-input", Input).value
        log = self.query_one("#url-norm-log", RichLog)
        log.clear()

        if not url:
            log.write("[red]Please enter a URL.[/red]")
            return

        try:
            result = self.manager.normalize(url)
            log.write(result)
        except Exception as e:
            log.write(f"[red]Error: {e}[/red]")
