from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, DataTable, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.mime_lab import MimeLabManager


class MimeLabTab(Container):
    """
    Tab for MIME Type utilities and File Signature detection.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = MimeLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]MIME & Magic Number Laboratory[/bold]", classes="welcome-text")

            with TabbedContent():
                # Tab 1: Detect File
                with TabPane("Detect File Type", id="mime-tab-detect"):
                    with Horizontal(classes="stat-box"):
                        yield Input(placeholder="Enter file path relative to project...", id="mime-file-input")
                        yield Button("Detect", id="btn-mime-detect", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Analysis Results[/bold]")
                        yield DataTable(id="mime-detect-table")

                # Tab 2: Lookup
                with TabPane("Dictionary Lookup", id="mime-tab-lookup"):
                    with Horizontal(classes="stat-box"):
                        yield Label("Extension (e.g. .json):", classes="label")
                        yield Input(placeholder=".ext", id="mime-ext-input")
                        yield Button("Lookup Ext", id="btn-mime-lookup-ext", variant="primary")

                    with Horizontal(classes="stat-box"):
                        yield Label("MIME Type (e.g. text/html):", classes="label")
                        yield Input(placeholder="type/subtype", id="mime-type-input")
                        yield Button("Lookup MIME", id="btn-mime-lookup-type", variant="success")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Result[/bold]")
                        yield Label("...", id="mime-lookup-result")

    def on_mount(self) -> None:
        table = self.query_one("#mime-detect-table", DataTable)
        table.add_columns("Property", "Value")

    @on(Button.Pressed, "#btn-mime-detect")
    def on_detect(self) -> None:
        filepath_str = self.query_one("#mime-file-input", Input).value
        if not filepath_str:
            self.notify("Please enter a file path.", severity="warning")
            return

        # Resolve path
        path = self.project_dir / filepath_str

        table = self.query_one("#mime-detect-table", DataTable)
        table.clear()

        try:
            info = self.manager.detect_file(path)
            table.add_row("[bold cyan]Best Guess[/bold cyan]", f"[bold]{info['best_guess']}[/bold]")

            conf_color = "green"
            if "Low" in info['confidence']:
                conf_color = "red"
            elif "Medium" in info['confidence']:
                conf_color = "yellow"

            table.add_row("Confidence", f"[{conf_color}]{info['confidence']}[/{conf_color}]")
            table.add_row("By Extension", str(info['extension_based'] or 'Unknown'))
            table.add_row("By Magic Number", str(info['magic_based'] or 'Unknown'))
            table.add_row("File Size", f"{info['size_bytes']} bytes")

        except FileNotFoundError:
            self.notify("File not found.", severity="error")
            table.add_row("Error", "File not found.")
        except Exception as e:
            self.notify(f"Error reading file: {e}", severity="error")
            table.add_row("Error", str(e))

    @on(Button.Pressed, "#btn-mime-lookup-ext")
    def on_lookup_ext(self) -> None:
        ext = self.query_one("#mime-ext-input", Input).value
        result_lbl = self.query_one("#mime-lookup-result", Label)

        if not ext:
            result_lbl.update("Please enter an extension.")
            return

        mime = self.manager.lookup_by_extension(ext)
        if mime:
            result_lbl.update(f"[bold green]Found:[/bold green] {mime}")
        else:
            result_lbl.update(f"[red]No MIME type found for '{ext}'[/red]")

    @on(Button.Pressed, "#btn-mime-lookup-type")
    def on_lookup_type(self) -> None:
        mime = self.query_one("#mime-type-input", Input).value
        result_lbl = self.query_one("#mime-lookup-result", Label)

        if not mime:
            result_lbl.update("Please enter a MIME type.")
            return

        exts = self.manager.lookup_by_mime(mime)
        if exts:
            result_lbl.update(f"[bold green]Found Extensions:[/bold green] {', '.join(exts)}")
        else:
            result_lbl.update(f"[red]No extensions found for '{mime}'[/red]")
