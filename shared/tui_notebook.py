import asyncio
from pathlib import Path

from rich.syntax import Syntax
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, ListItem, ListView, RichLog

from shared.notebook_lab import NotebookLabManager


class NotebookListItem(ListItem):
    """Custom ListItem that holds a notebook path."""

    def __init__(self, *children, notebook_path: Path, **kwargs) -> None:
        super().__init__(*children, **kwargs)
        self.notebook_path = notebook_path


class NotebookLabTab(Container):
    """Tab for managing Jupyter Notebooks."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = NotebookLabManager(project_dir)
        self.selected_notebook = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: List of Notebooks
            with Vertical(id="notebook-list-container", classes="stat-box"):
                yield Label("[bold]Notebooks[/bold]")
                yield ListView(id="notebook-list")
                yield Button("Refresh", id="btn-notebook-refresh", variant="default")

            # Right Pane: Details, Preview, Actions
            with Vertical(id="notebook-details-container"):
                yield Label("[bold]Notebook Details[/bold]")
                yield Label("Select a notebook to view details.", id="notebook-header")

                with Horizontal(id="notebook-actions"):
                    yield Button("Inspect", id="btn-notebook-inspect", variant="primary", disabled=True)
                    yield Button("Clean Output", id="btn-notebook-clean", variant="warning", disabled=True)
                    yield Button("Convert to Script", id="btn-notebook-convert", variant="success", disabled=True)
                    yield Button("Audit", id="btn-notebook-audit", variant="error", disabled=True)

                yield Label("[bold]Output / Log[/bold]")
                yield RichLog(id="notebook-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.load_notebooks()

    def load_notebooks(self) -> None:
        list_view = self.query_one("#notebook-list", ListView)
        list_view.clear()

        notebooks = self.manager.list_notebooks()
        if not notebooks:
            list_view.append(ListItem(Label("No notebooks found.")))
            return

        for nb in notebooks:
            try:
                rel_path = nb.relative_to(self.project_dir)
            except ValueError:
                rel_path = nb

            item = NotebookListItem(Label(str(rel_path)), notebook_path=nb)
            list_view.append(item)

    @on(ListView.Selected, "#notebook-list")
    def on_notebook_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, NotebookListItem):
            self.selected_notebook = event.item.notebook_path
            self.update_header()
            self.enable_buttons()
            # Auto-inspect on select
            self.action_inspect()

    def update_header(self) -> None:
        if self.selected_notebook:
            header = self.query_one("#notebook-header", Label)
            header.update(f"[bold]{self.selected_notebook.name}[/bold]")

    def enable_buttons(self) -> None:
        self.query_one("#btn-notebook-inspect").disabled = False
        self.query_one("#btn-notebook-clean").disabled = False
        self.query_one("#btn-notebook-convert").disabled = False
        self.query_one("#btn-notebook-audit").disabled = False

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-notebook-refresh":
            self.load_notebooks()
            self.notify("Notebooks refreshed.")
        elif event.button.id == "btn-notebook-inspect":
            self.action_inspect()
        elif event.button.id == "btn-notebook-clean":
            await self.action_clean()
        elif event.button.id == "btn-notebook-convert":
            await self.action_convert()
        elif event.button.id == "btn-notebook-audit":
            self.action_audit()

    def action_inspect(self) -> None:
        if not self.selected_notebook:
            return

        log = self.query_one("#notebook-log", RichLog)
        log.clear()
        log.write(f"Inspecting {self.selected_notebook.name}...")

        info = self.manager.inspect_notebook(self.selected_notebook)
        if "error" in info:
            log.write(f"[bold red]Error:[/bold red] {info['error']}")
            return

        log.write(f"Kernel:   {info['kernel']}")
        log.write(f"Language: {info['language']} {info['version']}")
        log.write(f"Format:   v{info['nbformat']}")
        log.write("[bold]Cells:[/bold]")
        for k, v in info['cells'].items():
            log.write(f"  {k.capitalize()}: {v}")

    async def action_clean(self) -> None:
        if not self.selected_notebook:
            return

        log = self.query_one("#notebook-log", RichLog)
        log.write(f"\nCleaning {self.selected_notebook.name}...")
        self.notify("Cleaning notebook...")

        try:
            changed = await asyncio.to_thread(self.manager.clean_notebook, self.selected_notebook)
            if changed:
                log.write("[green]Notebook cleaned (outputs removed).[/green]")
                self.notify("Notebook cleaned.")
            else:
                log.write("[yellow]Notebook already clean or no changes needed.[/yellow]")
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Error: {e}", severity="error")

    async def action_convert(self) -> None:
        if not self.selected_notebook:
            return

        log = self.query_one("#notebook-log", RichLog)
        log.write(f"\nConverting {self.selected_notebook.name} to script...")
        self.notify("Converting notebook...")

        try:
            out_path = await asyncio.to_thread(self.manager.convert_to_script, self.selected_notebook)
            log.write(f"[green]Converted to: {out_path.name}[/green]")

            # Show preview of script
            content = out_path.read_text(encoding="utf-8")
            log.write(Syntax(content, "python", theme="monokai"))

            self.notify("Conversion complete.")
        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Error: {e}", severity="error")

    def action_audit(self) -> None:
        if not self.selected_notebook:
            return

        log = self.query_one("#notebook-log", RichLog)
        log.write(f"\nAuditing {self.selected_notebook.name}...")

        issues = self.manager.audit_notebook(self.selected_notebook)
        if not issues:
            log.write("[green]No issues found.[/green]")
            return

        log.write(f"[bold red]Found {len(issues)} issues:[/bold red]")
        for issue in issues:
            cell_info = f" (Cell {issue['cell']})" if issue.get('cell') != "Global" else ""
            log.write(f"  [{issue['type']}] {issue['message']}{cell_info}")
