from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, DirectoryTree, Input, Button, RichLog, TextArea
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.csv2toml_lab import Csv2TomlManager


class Csv2TomlTab(Container):
    """
    Interactive CSV to TOML Converter Tab.
    """
    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = Csv2TomlManager()
        self.current_file = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: File Browser
            with Vertical(id="csv2toml-sidebar", classes="stat-box"):
                yield Label("[bold]CSV Files[/bold]")
                yield DirectoryTree(str(self.project_dir), id="csv2toml-file-tree")

            # Center: CSV Input
            with Vertical(id="csv2toml-main"):
                yield Label("[bold]CSV Input[/bold]", id="lbl-csv2toml-input")
                yield TextArea(id="csv2toml-input-editor", language="csv")
                with Horizontal():
                    yield Label("Delimiter: ")
                    yield Input(placeholder=",", value=",", id="csv2toml-delimiter", classes="small-input")
                yield Button("Convert", id="btn-csv2toml-convert", variant="primary")

            # Right: TOML Output
            with Vertical(id="csv2toml-editor-pane", classes="stat-box"):
                yield Label("[bold]TOML Output[/bold]")
                yield TextArea(id="csv2toml-output-editor", language="toml", read_only=True)
                yield Button("Save TOML File", id="btn-csv2toml-save", variant="success", disabled=True)
                yield RichLog(id="csv2toml-log", wrap=True, highlight=True, markup=True)

    @on(DirectoryTree.FileSelected, "#csv2toml-file-tree")
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = Path(event.path)
        if path.suffix.lower() == ".csv":
            self.load_file(path)
        else:
            self.notify("Please select a .csv file.", severity="warning")

    def load_file(self, path: Path) -> None:
        self.current_file = path
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.query_one("#csv2toml-input-editor", TextArea).text = content
            self.query_one("#lbl-csv2toml-input", Label).update(f"[bold]CSV Input: {path.name}[/bold]")
            self.log_message(f"Loaded {path.name}")
        except Exception as e:
            self.log_message(f"[red]Error loading CSV: {e}[/red]")

    @on(Button.Pressed, "#btn-csv2toml-convert")
    def on_convert(self) -> None:
        csv_content = self.query_one("#csv2toml-input-editor", TextArea).text
        delimiter = self.query_one("#csv2toml-delimiter", Input).value or ","
        if not csv_content:
            self.notify("No CSV content to convert.", severity="warning")
            return

        try:
            toml_str = self.manager.convert(csv_content, delimiter=delimiter)
            self.query_one("#csv2toml-output-editor", TextArea).text = toml_str
            self.query_one("#btn-csv2toml-save").disabled = False
            self.log_message("Converted CSV to TOML.")
        except Exception as e:
            self.log_message(f"[red]Conversion Error: {e}[/red]")

    @on(Button.Pressed, "#btn-csv2toml-save")
    def on_save(self) -> None:
        if not self.current_file:
            self.notify("Load a file from the tree first.", severity="warning")
            return

        toml_str = self.query_one("#csv2toml-output-editor", TextArea).text
        out_path = self.current_file.with_suffix(".toml")

        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(toml_str)
            self.log_message(f"[green]Saved to {out_path.name}[/green]")
        except Exception as e:
            self.log_message(f"[red]Error saving file: {e}[/red]")

    def log_message(self, message: str) -> None:
        log = self.query_one("#csv2toml-log", RichLog)
        log.write(message)
