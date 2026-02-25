from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Button, Input, Select, Static, RichLog, DataTable
from textual import on, work
from textual.timer import Timer
from typing import Optional

from shared.dash_lab import DashLabManager, DashboardConfig, WidgetConfig


class MetricWidget(Static):
    """A widget displaying a single metric."""

    DEFAULT_CSS = """
    MetricWidget {
        background: $surface;
        border: solid $accent;
        padding: 1;
        height: 100%;
    }
    .metric-title {
        text-align: center;
        color: $text-muted;
        dock: top;
    }
    .metric-value {
        text-align: center;
        content-align: center middle;
        text-style: bold;
        color: $success;
        height: 1fr;
        text-opacity: 100%;
    }
    """

    def __init__(self, config: WidgetConfig, manager: DashLabManager, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.manager = manager
        self.timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        yield Label(self.config.title, classes="metric-title")
        yield Label("Loading...", classes="metric-value", id=f"val-{self.id}")

    def on_mount(self) -> None:
        self.refresh_data()
        self.timer = self.set_interval(self.config.refresh_interval, self.refresh_data)

    @work(exclusive=True)
    async def refresh_data(self) -> None:
        value = await self.manager.execute_source(self.config)
        # Truncate if too long
        if len(value) > 50:
            value = value[:47] + "..."

        lbl = self.query_one(f"#val-{self.id}", Label)
        lbl.update(value)


class LogWidget(Container):
    """A widget displaying logs."""

    DEFAULT_CSS = """
    LogWidget {
        background: $surface;
        border: solid $accent;
        padding: 0;
        height: 100%;
    }
    .log-header {
        background: $accent;
        color: $text-on-accent;
        padding-left: 1;
        dock: top;
    }
    RichLog {
        background: $surface;
        min-height: 1;
    }
    """

    def __init__(self, config: WidgetConfig, manager: DashLabManager, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.manager = manager
        self.timer: Optional[Timer] = None

    def compose(self) -> ComposeResult:
        yield Label(self.config.title, classes="log-header")
        yield RichLog(id=f"log-{self.id}", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        self.refresh_data()
        self.timer = self.set_interval(self.config.refresh_interval, self.refresh_data)

    @work(exclusive=True)
    async def refresh_data(self) -> None:
        content = await self.manager.execute_source(self.config)
        log = self.query_one(f"#log-{self.id}", RichLog)
        # Clear logic? For now, we append if it looks like a stream, or replace?
        # DashLab execute_source reads the whole file/command output.
        # So we should clear and write.
        log.clear()
        log.write(content)


class DashboardRunner(Container):
    """Renders the dashboard widgets."""

    DEFAULT_CSS = """
    DashboardRunner {
        layout: grid;
        grid-size: 4 4; /* Default 4x4 grid */
        grid-gutter: 1;
        padding: 1;
    }
    """

    def __init__(self, config: DashboardConfig, manager: DashLabManager, **kwargs):
        super().__init__(**kwargs)
        self.dashboard_config = config
        self.manager = manager

    def compose(self) -> ComposeResult:
        for i, w_conf in enumerate(self.dashboard_config.widgets):
            widget_id = f"widget-{i}"
            if w_conf.type == "metric":
                w = MetricWidget(w_conf, self.manager, id=widget_id)
            elif w_conf.type == "log":
                w = LogWidget(w_conf, self.manager, id=widget_id)
            else:
                # Fallback to metric-like
                w = MetricWidget(w_conf, self.manager, id=widget_id)

            # Apply grid positioning
            # Note: Textual uses 1-based indexing for column/row start usually, but let's verify.
            # Actually, css is 1-based. Our config is likely 0-based.
            w.styles.grid_column_start = w_conf.col + 1
            w.styles.grid_row_start = w_conf.row + 1
            w.styles.grid_column_span = w_conf.col_span
            w.styles.grid_row_span = w_conf.row_span

            yield w


class DashEditor(Container):
    """Editor for the dashboard configuration."""

    def __init__(self, manager: DashLabManager, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.config = manager.load_config()

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Left: Widget List
            with Vertical(classes="stat-box", id="editor-list-pane"):
                yield Label("[bold]Widgets[/bold]")
                yield DataTable(id="dash-widgets-table")
                with Horizontal():
                    yield Button("Add", id="btn-dash-add", variant="success")
                    yield Button("Remove", id="btn-dash-remove", variant="error")
                yield Button("Save Dashboard", id="btn-dash-save", variant="primary")

            # Right: Widget Details Form
            with VerticalScroll(classes="stat-box", id="editor-form-pane"):
                yield Label("[bold]Widget Properties[/bold]")
                yield Label("Title:")
                yield Input(id="inp-w-title")

                yield Label("Type:")
                yield Select.from_values(["metric", "log"], id="sel-w-type", value="metric")

                yield Label("Source Type:")
                yield Select.from_values(["command", "file"], id="sel-w-source", value="command")

                yield Label("Command / File Path:")
                yield Input(id="inp-w-cmd")

                with Horizontal():
                    yield Label("Row:")
                    yield Input(id="inp-w-row", type="integer", value="0")
                    yield Label("Col:")
                    yield Input(id="inp-w-col", type="integer", value="0")

                with Horizontal():
                    yield Label("Row Span:")
                    yield Input(id="inp-w-rowspan", type="integer", value="1")
                    yield Label("Col Span:")
                    yield Input(id="inp-w-colspan", type="integer", value="1")

                yield Label("Refresh Interval (s):")
                yield Input(id="inp-w-refresh", type="integer", value="5")

                yield Button("Update Widget", id="btn-dash-update-widget", variant="warning")

    def on_mount(self) -> None:
        table = self.query_one("#dash-widgets-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Title", "Type", "Pos")
        self.load_widgets()

    def load_widgets(self) -> None:
        table = self.query_one("#dash-widgets-table", DataTable)
        table.clear()

        for i, w in enumerate(self.config.widgets):
            pos = f"{w.row},{w.col} ({w.row_span}x{w.col_span})"
            table.add_row(w.title, w.type, pos, key=str(i))

    @on(DataTable.RowSelected, "#dash-widgets-table")
    def on_widget_selected(self, event: DataTable.RowSelected) -> None:
        idx = int(event.row_key.value)
        widget = self.config.widgets[idx]

        self.query_one("#inp-w-title", Input).value = widget.title
        self.query_one("#sel-w-type", Select).value = widget.type
        self.query_one("#sel-w-source", Select).value = widget.source
        self.query_one("#inp-w-cmd", Input).value = widget.command if widget.source == "command" else widget.file_path
        self.query_one("#inp-w-row", Input).value = str(widget.row)
        self.query_one("#inp-w-col", Input).value = str(widget.col)
        self.query_one("#inp-w-rowspan", Input).value = str(widget.row_span)
        self.query_one("#inp-w-colspan", Input).value = str(widget.col_span)
        self.query_one("#inp-w-refresh", Input).value = str(widget.refresh_interval)

    @on(Button.Pressed, "#btn-dash-add")
    def on_add(self) -> None:
        # Create default
        new_w = WidgetConfig(type="metric", title="New Widget", row=0, col=0)
        self.config.widgets.append(new_w)
        self.load_widgets()
        self.notify("Widget added.")

    @on(Button.Pressed, "#btn-dash-remove")
    def on_remove(self) -> None:
        table = self.query_one("#dash-widgets-table", DataTable)
        if table.cursor_row is None:
            return

        # Get key from selected row (which matches index)
        # Note: We need to be careful if list changes. Key approach is safer.
        # But here key IS the index at load time.
        # If we delete, keys might mismatch indices unless we reload properly.
        # Let's rely on cursor_row index assuming table matches list order.
        idx = table.cursor_row
        if 0 <= idx < len(self.config.widgets):
            del self.config.widgets[idx]
            self.load_widgets()
            self.notify("Widget removed.")

    @on(Button.Pressed, "#btn-dash-update-widget")
    def on_update(self) -> None:
        table = self.query_one("#dash-widgets-table", DataTable)
        if table.cursor_row is None:
            self.notify("No widget selected.", severity="warning")
            return

        idx = table.cursor_row
        if not (0 <= idx < len(self.config.widgets)):
            return

        w = self.config.widgets[idx]

        w.title = self.query_one("#inp-w-title", Input).value
        w.type = self.query_one("#sel-w-type", Select).value
        w.source = self.query_one("#sel-w-source", Select).value

        cmd_val = self.query_one("#inp-w-cmd", Input).value
        if w.source == "command":
            w.command = cmd_val
        else:
            w.file_path = cmd_val

        w.row = int(self.query_one("#inp-w-row", Input).value)
        w.col = int(self.query_one("#inp-w-col", Input).value)
        w.row_span = int(self.query_one("#inp-w-rowspan", Input).value)
        w.col_span = int(self.query_one("#inp-w-colspan", Input).value)
        w.refresh_interval = int(self.query_one("#inp-w-refresh", Input).value)

        self.load_widgets()
        self.notify("Widget updated.")

    @on(Button.Pressed, "#btn-dash-save")
    def on_save(self) -> None:
        self.manager.save_config(self.config)
        self.notify("Dashboard configuration saved.")


class DashLabTab(Container):
    """Main Tab for Dash Lab."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = DashLabManager(project_dir)
        self.mode = "run"  # "run" or "edit"

    def compose(self) -> ComposeResult:
        with Horizontal(id="dash-header", classes="stat-box"):
            yield Label("[bold]Dash Lab[/bold]", classes="welcome-text")
            yield Button("Edit Mode", id="btn-dash-mode", variant="default")
            yield Button("Reload", id="btn-dash-reload", variant="primary")

        # Container for content
        yield Container(id="dash-content")

    def on_mount(self) -> None:
        self.load_runner()

    def load_runner(self) -> None:
        content = self.query_one("#dash-content", Container)
        content.remove_children()

        config = self.manager.load_config()
        content.mount(DashboardRunner(config, self.manager))

        self.mode = "run"
        self.query_one("#btn-dash-mode", Button).label = "Edit Mode"

    def load_editor(self) -> None:
        content = self.query_one("#dash-content", Container)
        content.remove_children()

        content.mount(DashEditor(self.manager))

        self.mode = "edit"
        self.query_one("#btn-dash-mode", Button).label = "Run Mode"

    @on(Button.Pressed, "#btn-dash-mode")
    def on_toggle_mode(self) -> None:
        if self.mode == "run":
            self.load_editor()
        else:
            self.load_runner()

    @on(Button.Pressed, "#btn-dash-reload")
    def on_reload(self) -> None:
        if self.mode == "run":
            self.load_runner()
            self.notify("Dashboard reloaded.")
        else:
            # For editor, maybe reload config from disk?
            self.query_one(DashEditor).config = self.manager.load_config()
            self.query_one(DashEditor).load_widgets()
            self.notify("Editor reloaded from disk.")
