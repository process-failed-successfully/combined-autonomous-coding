from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Button, Static, Label
from textual.binding import Binding
from shared.zip_lab import ZipManager


class ZipLabApp(App):
    """Textual TUI for Zip Lab."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #main-container {
        height: 100%;
        layout: horizontal;
    }

    .panel {
        width: 50%;
        height: 100%;
        border: solid green;
        padding: 1;
    }

    .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .input-row {
        height: 3;
        margin-bottom: 1;
    }

    .input-label {
        width: 15;
        padding-top: 1;
    }

    Input {
        width: 1fr;
    }

    Button {
        width: 100%;
        margin-top: 1;
    }

    .status-area {
        height: 1fr;
        border: solid gray;
        padding: 1;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "focus_create", "Focus Create"),
        Binding("e", "focus_extract", "Focus Extract"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = ZipManager()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Vertical(classes="panel", id="create-panel"):
                yield Label("Create Archive", classes="title")
                with Horizontal(classes="input-row"):
                    yield Label("Inputs (CSV):", classes="input-label")
                    yield Input(placeholder="file1.txt, dir1, ...", id="create-inputs")
                with Horizontal(classes="input-row"):
                    yield Label("Output Zip:", classes="input-label")
                    yield Input(placeholder="archive.zip", id="create-output")
                yield Button("Create", id="btn-create", variant="success")
                yield Static("", id="create-status", classes="status-area")

            with Vertical(classes="panel", id="extract-panel"):
                yield Label("Extract Archive", classes="title")
                with Horizontal(classes="input-row"):
                    yield Label("Input Zip:", classes="input-label")
                    yield Input(placeholder="archive.zip", id="extract-input")
                with Horizontal(classes="input-row"):
                    yield Label("Output Dir:", classes="input-label")
                    yield Input(placeholder="./output", id="extract-output")
                yield Button("Extract", id="btn-extract", variant="primary")
                yield Static("", id="extract-status", classes="status-area")
        yield Footer()

    def action_focus_create(self):
        self.query_one("#create-inputs", Input).focus()

    def action_focus_extract(self):
        self.query_one("#extract-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-create":
            self._handle_create()
        elif event.button.id == "btn-extract":
            self._handle_extract()

    def _handle_create(self) -> None:
        inputs_str = self.query_one("#create-inputs", Input).value.strip()
        output_str = self.query_one("#create-output", Input).value.strip()
        status = self.query_one("#create-status", Static)

        if not inputs_str:
            status.update("[red]Error: Please provide input paths.[/red]")
            return

        input_paths = [Path(p.strip()) for p in inputs_str.split(",") if p.strip()]
        output_path = Path(output_str) if output_str else Path("archive.zip")

        try:
            final_path = self.manager.create(input_paths, output_path)
            status.update(f"[green]Success![/green]\nArchive created at: {final_path}")
        except Exception as e:
            status.update(f"[red]Error:[/red]\n{e}")

    def _handle_extract(self) -> None:
        input_str = self.query_one("#extract-input", Input).value.strip()
        output_str = self.query_one("#extract-output", Input).value.strip()
        status = self.query_one("#extract-status", Static)

        if not input_str:
            status.update("[red]Error: Please provide an input archive.[/red]")
            return

        input_path = Path(input_str)
        output_dir = Path(output_str) if output_str else Path(".")

        try:
            final_path = self.manager.extract(input_path, output_dir)
            status.update(f"[green]Success![/green]\nArchive extracted to: {final_path}")
        except Exception as e:
            status.update(f"[red]Error:[/red]\n{e}")
