import asyncio
from pathlib import Path
from typing import Any
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, Tree, RichLog
from textual import on

from shared.db_query import get_schema_info
from shared.schema_parser import SchemaParser


class DatabaseDiagramTab(Container):
    """Tab for visualizing Database Schema."""

    def __init__(self, project_dir: Path, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.parser = SchemaParser()
        self.schema_data: dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left Pane: Table Tree
            with Vertical(id="db-diag-left-pane", classes="stat-box"):
                yield Label("[bold]Tables & Columns[/bold]")
                yield Tree("Database Schema", id="db-diag-tree")
                yield Button("Refresh", id="btn-db-diag-refresh", variant="default")

            # Right Pane: Diagram/Details
            with Vertical(id="db-diag-right-pane"):
                yield Label("[bold]Relationships (Mermaid)[/bold]")
                yield RichLog(id="db-diag-mermaid", wrap=True, highlight=True, markup=True)

                with Horizontal(classes="stat-box"):
                    yield Button("Generate Mermaid", id="btn-db-diag-gen", variant="primary")
                    yield Button("Export to File", id="btn-db-diag-export", variant="success")

    def on_mount(self) -> None:
        self.load_schema()

    def load_schema(self) -> None:
        self.notify("Loading schema...")
        asyncio.create_task(self._load_schema_async())

    async def _load_schema_async(self) -> None:
        # get_schema_info might block if it searches files, run in thread
        try:
            schema_text, db_path = await asyncio.to_thread(get_schema_info, self.project_dir)

            if not schema_text:
                self.notify("No schema found.", severity="warning")
                self.query_one("#db-diag-mermaid", RichLog).write("No schema found. Ensure a SQLite DB exists.")
                return

            self.schema_data = self.parser.parse(schema_text)
            self._populate_tree()
            self._show_mermaid()
            self.notify("Schema loaded.")
        except Exception as e:
            self.notify(f"Error loading schema: {e}", severity="error")

    def _populate_tree(self) -> None:
        tree = self.query_one("#db-diag-tree", Tree)
        tree.clear()
        tree.root.expand()

        for table in self.schema_data.get("tables", []):
            t_node = tree.root.add(f"📄 {table['name']}", expand=True)
            for col in table["columns"]:
                # Check if this column is a FK
                is_fk = any(fk["from_col"] == col["name"] for fk in table["fks"])
                icon = "🔑" if is_fk else "🔹"
                t_node.add(f"{icon} {col['name']} ({col['type']})")

    def _show_mermaid(self) -> None:
        if not self.schema_data:
            return

        mermaid = self.parser.generate_mermaid(self.schema_data)
        log = self.query_one("#db-diag-mermaid", RichLog)
        log.clear()
        log.write(mermaid)

    @on(Button.Pressed, "#btn-db-diag-refresh")
    def on_refresh(self) -> None:
        self.load_schema()

    @on(Button.Pressed, "#btn-db-diag-gen")
    def on_generate(self) -> None:
        self._show_mermaid()
        self.notify("Diagram generated.")

    @on(Button.Pressed, "#btn-db-diag-export")
    def on_export(self) -> None:
        if not self.schema_data:
            self.notify("No schema to export.", severity="error")
            return

        mermaid = self.parser.generate_mermaid(self.schema_data)
        output_path = self.project_dir / "db_schema.mermaid"
        try:
            output_path.write_text(mermaid, encoding="utf-8")
            self.notify(f"Exported to {output_path.name}")
        except Exception as e:
            self.notify(f"Error exporting: {e}", severity="error")
