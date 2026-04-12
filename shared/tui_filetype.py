from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, Input, Static
from textual import on
from shared.filetype_lab import FileTypeManager

class FileTypeLabTab(Container):
    """Tab for FileType Lab (detect file types using magic bytes)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = FileTypeManager()

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-4"):
            yield Label("[bold]FileType Lab (Magic Bytes)[/bold]", classes="welcome-text mb-4")

            with Horizontal(classes="mb-4"):
                yield Label("File Path: ", classes="mr-2 mt-1")
                yield Input(placeholder="/path/to/file", id="input-filepath")
                yield Button("Detect", id="btn-detect", variant="primary", classes="ml-2")

            with Vertical(id="result-container", classes="stat-box p-4"):
                yield Static(id="output-result")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-detect":
            self.detect_file()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "input-filepath":
            self.detect_file()

    def detect_file(self) -> None:
        filepath = self.query_one("#input-filepath", Input).value.strip()
        output_widget = self.query_one("#output-result", Static)

        if not filepath:
            output_widget.update("[red]Error: Please enter a file path.[/red]")
            return

        result = self.manager.detect(filepath)

        if "error" in result:
            output_widget.update(f"[red]{result['error']}[/red]")
        else:
            output = f"[bold green]File detected![/bold green]\n\n"
            output += f"[bold]Extension:[/bold] {result.get('ext', 'N/A')}\n"
            output += f"[bold]MIME Type:[/bold] {result.get('mime', 'N/A')}\n"
            output += f"[bold]Description:[/bold] {result.get('desc', 'N/A')}"
            output_widget.update(output)
