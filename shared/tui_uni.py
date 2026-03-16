from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Label, Input, Button, DataTable, RichLog, Select
from textual import on
from shared.uni_lab import UniLabManager

class UniLabTab(Container):
    """Tab for Unicode Lab operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = UniLabManager()

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("[bold]Unicode Lab[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical():
                    yield Label("Operation:")
                    yield Select.from_values(
                        ["Inspect", "Search", "Escape", "Unescape"],
                        id="uni-operation-select",
                        value="Inspect"
                    )

            # --- Inspect Section ---
            with Container(id="uni-inspect-container", classes="stat-box"):
                with Horizontal():
                    yield Input(placeholder="Enter text to inspect...", id="uni-inspect-input")
                    yield Button("Inspect", id="uni-inspect-btn", variant="primary")

                yield DataTable(id="uni-inspect-table")

            # --- Search Section ---
            with Container(id="uni-search-container", classes="stat-box"):
                with Horizontal():
                    yield Input(placeholder="Enter Unicode character name (e.g. GRINNING FACE)...", id="uni-search-input")
                    yield Input(placeholder="Limit (default 50)", id="uni-search-limit", type="integer", value="50")
                    yield Button("Search", id="uni-search-btn", variant="primary")

                yield DataTable(id="uni-search-table")

            # --- Escape/Unescape Section ---
            with Container(id="uni-escape-container", classes="stat-box"):
                with Horizontal():
                    yield Input(placeholder="Enter text...", id="uni-escape-input")
                    yield Button("Execute", id="uni-escape-btn", variant="primary")

                yield RichLog(id="uni-escape-log", markup=True, wrap=True)


    def on_mount(self) -> None:
        inspect_table = self.query_one("#uni-inspect-table", DataTable)
        inspect_table.add_columns("Char", "Code", "Cat", "UTF-8", "Name")

        search_table = self.query_one("#uni-search-table", DataTable)
        search_table.add_columns("Char", "Code", "Name")

        # Hide non-inspect containers on mount
        self.query_one("#uni-search-container").display = False
        self.query_one("#uni-escape-container").display = False

    @on(Select.Changed, "#uni-operation-select")
    def on_operation_changed(self, event: Select.Changed) -> None:
        op = str(event.value).lower()

        self.query_one("#uni-inspect-container").display = (op == "inspect")
        self.query_one("#uni-search-container").display = (op == "search")
        self.query_one("#uni-escape-container").display = (op in ["escape", "unescape"])

    @on(Button.Pressed, "#uni-inspect-btn")
    def on_inspect_pressed(self, event: Button.Pressed) -> None:
        text = self.query_one("#uni-inspect-input", Input).value
        table = self.query_one("#uni-inspect-table", DataTable)
        table.clear()

        if not text:
            return

        try:
            results = self.manager.inspect(text)
            for item in results:
                display_char = item['char']
                if display_char.isspace():
                    if display_char == ' ':
                        display_char = "' '"
                    else:
                        display_char = repr(display_char)
                elif item['category'].startswith('C'):
                    display_char = ""

                table.add_row(display_char, item['code_point'], item['category'], item['utf8'], item['name'])
        except Exception as e:
            pass

    @on(Button.Pressed, "#uni-search-btn")
    def on_search_pressed(self, event: Button.Pressed) -> None:
        query = self.query_one("#uni-search-input", Input).value
        limit_str = self.query_one("#uni-search-limit", Input).value
        table = self.query_one("#uni-search-table", DataTable)
        table.clear()

        if not query:
            return

        try:
            limit = int(limit_str) if limit_str.isdigit() else 50
            results = self.manager.search(query, limit=limit)
            for res in results:
                table.add_row(res['char'], res['code_point'], res['name'])
        except Exception as e:
            pass

    @on(Button.Pressed, "#uni-escape-btn")
    def on_escape_pressed(self, event: Button.Pressed) -> None:
        op = str(self.query_one("#uni-operation-select", Select).value).lower()
        text = self.query_one("#uni-escape-input", Input).value
        log = self.query_one("#uni-escape-log", RichLog)

        if not text:
            log.write("[yellow]Please enter text.[/yellow]")
            return

        try:
            if op == "escape":
                result = self.manager.escape(text)
            elif op == "unescape":
                result = self.manager.unescape(text)
            else:
                return

            from rich.markup import escape
            log.write(f"[green]Success:[/green]\n{escape(result)}\n")
        except Exception as e:
            log.write(f"[red]Error:[/red] {e}")
