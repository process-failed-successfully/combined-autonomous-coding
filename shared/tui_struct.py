from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Input, Button, DataTable, TabbedContent, TabPane, Static
from textual import on
from shared.struct_lab import StructLabManager

class StructLabTab(Container):
    """Tab for Struct Lab operations."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = StructLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Struct Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                with TabPane("Calculator", id="tab-struct-calc"):
                    with Container(classes="stat-box"):
                        yield Label("Format String (e.g. 'i4s'):")
                        yield Input(placeholder="Format...", id="struct-calc-fmt")
                        yield Button("Calculate Size", id="btn-struct-calc", variant="primary")
                        yield Label("", id="struct-calc-result", classes="value")

                with TabPane("Hex Dump", id="tab-struct-hex"):
                    with Vertical(classes="stat-box"):
                        yield Label("File Path:")
                        yield Input(placeholder="Path to file...", id="struct-hex-path")
                        with Horizontal():
                            with Vertical(classes="column"):
                                yield Label("Offset (dec/hex):")
                                yield Input(placeholder="0", id="struct-hex-offset", value="0")
                            with Vertical(classes="column"):
                                yield Label("Length (optional):")
                                yield Input(placeholder="Bytes to read...", id="struct-hex-len")

                        yield Button("Hex Dump", id="btn-struct-hex", variant="primary")

                    yield DataTable(id="struct-hex-table")

                with TabPane("Unpack", id="tab-struct-unpack"):
                    with Vertical(classes="stat-box"):
                        yield Label("File Path:")
                        yield Input(placeholder="Path to file...", id="struct-unpack-path")
                        yield Label("Format String:")
                        yield Input(placeholder="e.g. 'i4s'...", id="struct-unpack-fmt")
                        yield Label("Offset:")
                        yield Input(placeholder="0", id="struct-unpack-offset", value="0")

                        yield Button("Unpack", id="btn-struct-unpack", variant="primary")

                    yield DataTable(id="struct-unpack-table")

                with TabPane("Pack", id="tab-struct-pack"):
                    with Vertical(classes="stat-box"):
                        yield Label("Format String:")
                        yield Input(placeholder="e.g. 'i4s'...", id="struct-pack-fmt")
                        yield Label("Values (comma separated):")
                        yield Input(placeholder="123, hello...", id="struct-pack-values")
                        yield Label("Output Path:")
                        yield Input(placeholder="Path to output file...", id="struct-pack-out")

                        yield Button("Pack", id="btn-struct-pack", variant="warning")
                        yield Label("", id="struct-pack-result")

    def on_mount(self) -> None:
        # Hex Table
        hex_table = self.query_one("#struct-hex-table", DataTable)
        hex_table.cursor_type = "row"
        hex_table.add_columns("Offset", "Hex", "ASCII")

        # Unpack Table
        unpack_table = self.query_one("#struct-unpack-table", DataTable)
        unpack_table.cursor_type = "row"
        unpack_table.add_columns("Index", "Type", "Value")

    @on(Button.Pressed, "#btn-struct-calc")
    def on_calc_size(self) -> None:
        fmt = self.query_one("#struct-calc-fmt", Input).value
        res_lbl = self.query_one("#struct-calc-result", Label)

        if not fmt:
            res_lbl.update("[red]Format required.[/red]")
            return

        try:
            size = self.manager.calc_size(fmt)
            res_lbl.update(f"Size: [bold green]{size} bytes[/bold green]")
        except Exception as e:
            res_lbl.update(f"[red]Error: {e}[/red]")

    @on(Button.Pressed, "#btn-struct-hex")
    def on_hex_dump(self) -> None:
        path_str = self.query_one("#struct-hex-path", Input).value
        offset_str = self.query_one("#struct-hex-offset", Input).value
        len_str = self.query_one("#struct-hex-len", Input).value

        table = self.query_one("#struct-hex-table", DataTable)
        table.clear()

        if not path_str:
            self.notify("File path required.", severity="error")
            return

        path = self.project_dir / path_str

        try:
            offset = int(offset_str, 0) if offset_str else 0
            length = int(len_str) if len_str else None

            rows = self.manager.get_hex_dump(path, offset, length)

            if not rows:
                self.notify("No data read.", severity="warning")
                return

            for row in rows:
                table.add_row(row["offset"], row["hex"], row["ascii"])

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    @on(Button.Pressed, "#btn-struct-unpack")
    def on_unpack(self) -> None:
        path_str = self.query_one("#struct-unpack-path", Input).value
        fmt = self.query_one("#struct-unpack-fmt", Input).value
        offset_str = self.query_one("#struct-unpack-offset", Input).value

        table = self.query_one("#struct-unpack-table", DataTable)
        table.clear()

        if not path_str or not fmt:
            self.notify("Path and Format required.", severity="error")
            return

        path = self.project_dir / path_str

        try:
            offset = int(offset_str, 0) if offset_str else 0
            values = self.manager.unpack_data(fmt, path, offset)

            for i, val in enumerate(values):
                val_type = type(val).__name__
                # Format bytes for display
                if isinstance(val, bytes):
                    display_val = str(val)
                else:
                    display_val = str(val)

                table.add_row(str(i), val_type, display_val)

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    @on(Button.Pressed, "#btn-struct-pack")
    def on_pack(self) -> None:
        fmt = self.query_one("#struct-pack-fmt", Input).value
        values_str = self.query_one("#struct-pack-values", Input).value
        out_str = self.query_one("#struct-pack-out", Input).value

        res_lbl = self.query_one("#struct-pack-result", Label)

        if not fmt or not values_str or not out_str:
            res_lbl.update("[red]All fields required.[/red]")
            return

        out_path = self.project_dir / out_str
        # Split by comma, respecting potential quotes might be needed but simple split for now
        # Ideally use csv reader for robustness, but simple split matches likely use case
        values = [v.strip() for v in values_str.split(",")]

        try:
            bytes_written = self.manager.pack_data(fmt, values, out_path)
            res_lbl.update(f"[green]Packed {bytes_written} bytes to {out_path.name}[/green]")
            self.notify(f"Packed {bytes_written} bytes.")
        except Exception as e:
            res_lbl.update(f"[red]Error: {e}[/red]")
