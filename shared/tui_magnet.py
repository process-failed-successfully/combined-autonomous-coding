import json
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, TabbedContent, TabPane, TextArea
from shared.magnet_lab import MagnetLabManager

class MagnetLabTab(Container):
    """Tab for interactive Magnet URI operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(id="tab-magnet", **kwargs)
        self.manager = MagnetLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Magnet Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Parse Pane
                with TabPane("Parse URI"):
                    with Vertical(classes="stat-box"):
                        yield Label("Magnet URI:")
                        yield Input(placeholder="magnet:?xt=urn:btih:...", id="magnet-parse-input")

                        yield Button("Parse", id="btn-magnet-parse", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Parsed Result[/bold]")
                        yield RichLog(id="magnet-parse-result", wrap=True, highlight=True, markup=True)

                # Build Pane
                with TabPane("Build URI"):
                    with Vertical(classes="stat-box"):
                        yield Label("Exact Topic (xt):")
                        yield Input(placeholder="e.g. urn:btih:1234567890abcdef...", id="magnet-build-xt")

                        yield Label("Display Name (dn):")
                        yield Input(placeholder="e.g. Ubuntu 22.04 ISO", id="magnet-build-dn")

                        yield Label("Trackers (tr) - one per line:")
                        yield TextArea(id="magnet-build-tr")

                        yield Button("Build URI", id="btn-magnet-build", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Generated URI[/bold]")
                        yield RichLog(id="magnet-build-result", wrap=True, highlight=True, markup=True)

                # From Torrent Pane
                with TabPane("From Torrent"):
                    with Vertical(classes="stat-box"):
                        yield Label("Path to .torrent file:")
                        yield Input(placeholder="/path/to/file.torrent", id="magnet-torrent-path")

                        yield Button("Generate from Torrent", id="btn-magnet-torrent", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="magnet-torrent-result", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-magnet-parse":
            self.do_parse()
        elif event.button.id == "btn-magnet-build":
            self.do_build()
        elif event.button.id == "btn-magnet-torrent":
            self.do_from_torrent()

    def do_parse(self) -> None:
        uri = self.query_one("#magnet-parse-input", Input).value
        result_log = self.query_one("#magnet-parse-result", RichLog)

        result_log.clear()

        if not uri:
            self.notify("Please enter a Magnet URI.", severity="error")
            return

        res = self.manager.parse(uri)
        if res.get("success"):
            result_log.write(json.dumps(res["parsed"], indent=2))
        else:
            from rich.markup import escape
            safe_error = escape(str(res.get('error')))
            result_log.write(f"[bold red]Error:[/bold red] {safe_error}")
            self.notify("Failed to parse URI.", severity="error")

    def do_build(self) -> None:
        xt = self.query_one("#magnet-build-xt", Input).value
        dn = self.query_one("#magnet-build-dn", Input).value
        tr_text = self.query_one("#magnet-build-tr", TextArea).text
        result_log = self.query_one("#magnet-build-result", RichLog)

        result_log.clear()

        if not xt and not dn and not tr_text:
            self.notify("Please provide at least one parameter to build.", severity="error")
            return

        params = {}
        if xt:
            params["xt"] = xt
        if dn:
            params["dn"] = dn

        tr_list = [line.strip() for line in tr_text.split("\n") if line.strip()]
        if tr_list:
            params["tr"] = tr_list

        uri = self.manager.build(params)
        result_log.write(uri)

    def do_from_torrent(self) -> None:
        path = self.query_one("#magnet-torrent-path", Input).value
        result_log = self.query_one("#magnet-torrent-result", RichLog)

        result_log.clear()

        if not path:
            self.notify("Please provide a path to a .torrent file.", severity="error")
            return

        res = self.manager.from_torrent(path)
        if res.get("success"):
            result_log.write(f"[bold green]Magnet URI:[/bold green]\n{res['uri']}\n")
            result_log.write(f"[bold]Info Hash:[/bold] {res['info_hash']}")
            if res.get("name"):
                result_log.write(f"[bold]Name:[/bold] {res['name']}")
            if res.get("trackers"):
                result_log.write("[bold]Trackers:[/bold]")
                for t in res["trackers"]:
                    result_log.write(f"  - {t}")
        else:
            from rich.markup import escape
            safe_error = escape(str(res.get('error')))
            result_log.write(f"[bold red]Error:[/bold red] {safe_error}")
            self.notify("Failed to generate from torrent.", severity="error")
