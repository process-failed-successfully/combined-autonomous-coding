from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, Static, Label, TabPane
from textual.reactive import reactive
import json
from shared.magnet_lab import MagnetLabManager

class MagnetLabTab(TabPane):
    """TUI Tab for Magnet Lab."""

    def __init__(self, *args, **kwargs):
        super().__init__("Magnet", id="magnet-lab-tab", **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-4"):
            yield Label("Magnet URI parsing and building", classes="text-xl mb-4")

            with Horizontal(classes="mb-2 h-auto"):
                yield Input(placeholder="Enter Magnet URI to parse...", id="magnet-parse-input", classes="w-2/3")
                yield Button("Parse", id="magnet-btn-parse", variant="primary", classes="w-1/3")

            yield Label("Parsed Data / Output", classes="mt-4 mb-2")
            yield Static("", id="magnet-output", classes="border border-green-500 p-2 h-auto min-h-[10]")

            yield Label("Build Magnet URI", classes="text-xl mt-4 mb-2")
            with Horizontal(classes="mb-2 h-auto"):
                yield Input(placeholder="Exact Topic (xt) e.g., urn:btih:...", id="magnet-build-xt", classes="w-1/3")
                yield Input(placeholder="Display Name (dn)", id="magnet-build-dn", classes="w-1/3")
                yield Input(placeholder="Trackers (tr) comma-separated", id="magnet-build-tr", classes="w-1/3")
            with Horizontal(classes="mb-2 h-auto"):
                yield Button("Build", id="magnet-btn-build", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "magnet-btn-parse":
            self._handle_parse()
        elif event.button.id == "magnet-btn-build":
            self._handle_build()

    def _handle_parse(self) -> None:
        input_widget = self.query_one("#magnet-parse-input", Input)
        output_widget = self.query_one("#magnet-output", Static)

        uri = input_widget.value.strip()
        if not uri:
            output_widget.update("[red]Error: Please enter a Magnet URI.[/red]")
            return

        try:
            manager = MagnetLabManager()
            result = manager.parse(uri)
            output_widget.update(json.dumps(result, indent=2))
        except Exception as e:
             # Need to safely format errors to prevent markup issues
             from rich.markup import escape
             output_widget.update(f"[red]Error parsing URI: {escape(str(e))}[/red]")

    def _handle_build(self) -> None:
        xt_widget = self.query_one("#magnet-build-xt", Input)
        dn_widget = self.query_one("#magnet-build-dn", Input)
        tr_widget = self.query_one("#magnet-build-tr", Input)
        output_widget = self.query_one("#magnet-output", Static)

        xt = xt_widget.value.strip()
        dn = dn_widget.value.strip() or None
        tr_str = tr_widget.value.strip()

        tr = [t.strip() for t in tr_str.split(",")] if tr_str else None

        if not xt:
            output_widget.update("[red]Error: Exact Topic (xt) is required to build a Magnet URI.[/red]")
            return

        try:
            manager = MagnetLabManager()
            result = manager.build(xt=xt, dn=dn, tr=tr)
            output_widget.update(f"[green]{result}[/green]")
        except Exception as e:
            from rich.markup import escape
            output_widget.update(f"[red]Error building URI: {escape(str(e))}[/red]")

def run_tui():
    from textual.app import App
    from textual.widgets import Header, Footer, TabbedContent

    class MagnetApp(App):
        CSS = """
        .p-4 { padding: 1; }
        .mb-2 { margin-bottom: 1; }
        .mb-4 { margin-bottom: 2; }
        .mt-4 { margin-top: 2; }
        .w-1_3 { width: 33%; }
        .w-2_3 { width: 67%; }
        .h-auto { height: auto; }
        .min-h-[10] { min-height: 10; }
        .border { border: solid; }
        .border-green-500 { border: solid green; }
        """
        def compose(self) -> ComposeResult:
            yield Header()
            with TabbedContent():
                yield MagnetLabTab()
            yield Footer()

    app = MagnetApp()
    app.run()
