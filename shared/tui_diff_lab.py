import json
import yaml
import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Select, DataTable, RichLog, TextArea, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from rich.syntax import Syntax
from shared.diff_lab import DiffLabManager

class DiffLabTab(Container):
    """Tab for Diff Lab operations."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = DiffLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Diff Lab[/bold]", classes="welcome-text")

            # Inputs Area
            with Horizontal(classes="diff-inputs-container"):
                # Left Input
                with Vertical(classes="stat-box diff-input-box"):
                    yield Label("Source A (Left)")
                    with Horizontal():
                        yield Input(placeholder="File Path...", id="input-diff-path-a")
                        yield Button("Load", id="btn-diff-load-a", variant="default")
                    yield TextArea(id="text-diff-a", language="python") # Default language

                # Right Input
                with Vertical(classes="stat-box diff-input-box"):
                    yield Label("Source B (Right)")
                    with Horizontal():
                        yield Input(placeholder="File Path...", id="input-diff-path-b")
                        yield Button("Load", id="btn-diff-load-b", variant="default")
                    yield TextArea(id="text-diff-b", language="python")

            # Controls
            with Horizontal(classes="stat-box"):
                yield Button("Compare", id="btn-diff-compare", variant="primary")
                yield Label("Mode:")
                yield Select.from_values(["Text", "JSON", "YAML"], id="select-diff-mode", value="Text")
                yield Button("Clear", id="btn-diff-clear", variant="error")

            # Output
            with TabbedContent(id="diff-output-tabs"):
                with TabPane("Unified Diff", id="tab-diff-text"):
                    yield RichLog(id="diff-result-log", wrap=True, highlight=False, markup=False)
                with TabPane("Structural Diff", id="tab-diff-struct"):
                    yield DataTable(id="diff-result-table")
                with TabPane("Directory Diff", id="tab-diff-dir"):
                    with Vertical():
                        with Horizontal(classes="stat-box"):
                            yield Input(placeholder="Dir A Path...", id="input-diff-dir-a")
                            yield Input(placeholder="Dir B Path...", id="input-diff-dir-b")
                            yield Button("Compare Dirs", id="btn-diff-compare-dirs", variant="primary")
                        yield DataTable(id="diff-dir-result-table")

    def on_mount(self) -> None:
        table = self.query_one("#diff-result-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Path", "Type", "Old Value", "New Value")

        dir_table = self.query_one("#diff-dir-result-table", DataTable)
        dir_table.cursor_type = "row"
        dir_table.add_columns("Status", "Path")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-diff-load-a":
            await self.load_file("a")
        elif event.button.id == "btn-diff-load-b":
            await self.load_file("b")
        elif event.button.id == "btn-diff-compare":
            self.compare()
        elif event.button.id == "btn-diff-compare-dirs":
            await self.compare_dirs()
        elif event.button.id == "btn-diff-clear":
            self.clear_inputs()

    async def load_file(self, side: str) -> None:
        path_input = self.query_one(f"#input-diff-path-{side}", Input)
        text_area = self.query_one(f"#text-diff-{side}", TextArea)

        path_str = path_input.value
        if not path_str:
            self.notify("Please enter a file path.", severity="error")
            return

        path = self.project_dir / path_str
        if not path.exists():
            self.notify(f"File not found: {path}", severity="error")
            return

        try:
            content = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="replace")
            text_area.text = content
            self.notify(f"Loaded {path.name}")

            # Auto-detect language for highlighting
            suffix = path.suffix.lower()
            if suffix in ['.json']:
                text_area.language = "json"
            elif suffix in ['.yaml', '.yml']:
                text_area.language = "yaml"
            elif suffix in ['.py']:
                text_area.language = "python"
            elif suffix in ['.md']:
                text_area.language = "markdown"
            else:
                text_area.language = None

        except Exception as e:
            self.notify(f"Error reading file: {e}", severity="error")

    def compare(self) -> None:
        text_a = self.query_one("#text-diff-a", TextArea).text
        text_b = self.query_one("#text-diff-b", TextArea).text
        mode = self.query_one("#select-diff-mode", Select).value

        log = self.query_one("#diff-result-log", RichLog)
        log.clear()

        table = self.query_one("#diff-result-table", DataTable)
        table.clear()

        if mode == "Text":
            self._compare_text(text_a, text_b, log)
            self.query_one("#diff-output-tabs", TabbedContent).active = "tab-diff-text"

        elif mode in ["JSON", "YAML"]:
            self._compare_structured(text_a, text_b, mode, table, log)
            self.query_one("#diff-output-tabs", TabbedContent).active = "tab-diff-struct"

    def _compare_text(self, text_a: str, text_b: str, log: RichLog) -> None:
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)

        diff = self.manager.get_text_diff(lines_a, lines_b, fromfile="Left", tofile="Right")

        if not diff:
            log.write("[green]No differences found.[/green]")
        else:
            diff_text = "".join(diff)
            log.write(Syntax(diff_text, "diff", theme="monokai", line_numbers=True))

    def _compare_structured(self, text_a: str, text_b: str, mode: str, table: DataTable, log: RichLog) -> None:
        try:
            data_a = self._parse_data(text_a, mode)
            data_b = self._parse_data(text_b, mode)
        except Exception as e:
            log.write(f"[red]Error parsing {mode}: {e}[/red]")
            # Switch to log view to show error
            self.query_one("#diff-output-tabs", TabbedContent).active = "tab-diff-text"
            return

        diffs = self.manager.get_structure_diff(data_a, data_b)

        if not diffs:
            log.write("[green]Structures are identical.[/green]")
            self.query_one("#diff-output-tabs", TabbedContent).active = "tab-diff-text"
            return

        for d in diffs:
            path = "root" + d['path']

            # Format values
            old_val = json.dumps(d.get('old'), default=str) if 'old' in d else "-"
            new_val = json.dumps(d.get('new'), default=str) if 'new' in d else "-"

            # Truncate
            if len(old_val) > 50: old_val = old_val[:47] + "..."
            if len(new_val) > 50: new_val = new_val[:47] + "..."

            # Color code type
            d_type = d['type']
            if "ADDED" in d_type:
                d_type = f"[green]{d_type}[/green]"
            elif "REMOVED" in d_type:
                d_type = f"[red]{d_type}[/red]"
            elif "MODIFIED" in d_type:
                d_type = f"[yellow]{d_type}[/yellow]"

            table.add_row(path, d_type, old_val, new_val)

    def _parse_data(self, text: str, mode: str):
        if mode == "JSON":
            return json.loads(text)
        elif mode == "YAML":
            return yaml.safe_load(text)
        return None

    async def compare_dirs(self) -> None:
        dir_a_str = self.query_one("#input-diff-dir-a", Input).value
        dir_b_str = self.query_one("#input-diff-dir-b", Input).value
        dir_table = self.query_one("#diff-dir-result-table", DataTable)

        dir_table.clear()

        if not dir_a_str or not dir_b_str:
            self.notify("Please enter both directory paths.", severity="error")
            return

        dir_a = self.project_dir / dir_a_str
        dir_b = self.project_dir / dir_b_str

        if not dir_a.is_dir() or not dir_b.is_dir():
            self.notify("One or both paths are not valid directories.", severity="error")
            return

        try:
            results = await asyncio.to_thread(self.manager.compare_directories, dir_a, dir_b, True)
            if results is not None:
                for res in results:
                    status = res["status"]
                    style = ""
                    if status == "Added": style = "[green]"
                    elif status == "Removed": style = "[red]"
                    elif status == "Modified": style = "[yellow]"
                    elif status == "Identical": style = "[dim]"

                    styled_status = f"{style}{status}{'[/]' if style else ''}"
                    dir_table.add_row(styled_status, res["path"])
                self.notify(f"Directory comparison complete. Found {len(results)} items.")
        except Exception as e:
            self.notify(f"Error comparing directories: {e}", severity="error")

    def clear_inputs(self) -> None:
        self.query_one("#text-diff-a", TextArea).text = ""
        self.query_one("#text-diff-b", TextArea).text = ""
        self.query_one("#input-diff-path-a", Input).value = ""
        self.query_one("#input-diff-path-b", Input).value = ""
        self.query_one("#input-diff-dir-a", Input).value = ""
        self.query_one("#input-diff-dir-b", Input).value = ""
        self.query_one("#diff-result-log", RichLog).clear()
        self.query_one("#diff-result-table", DataTable).clear()
        self.query_one("#diff-dir-result-table", DataTable).clear()
        self.notify("Inputs cleared.")
