from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, DataTable, RichLog, TabbedContent, TabPane, Static, Select
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.path_lab import PathLabManager

class PathLabTab(Container):
    """Tab for Path Inspection and Calculation."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = PathLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Path Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # INSPECTOR
                with TabPane("Inspector"):
                    with Vertical(classes="stat-box"):
                        yield Label("Path to Inspect:")
                        with Horizontal():
                            yield Input(placeholder="Enter path...", id="path-inspect-input")
                            yield Button("Inspect", id="btn-path-inspect", variant="primary")

                        yield DataTable(id="path-inspect-table")

                # CALCULATOR
                with TabPane("Calculator"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Path Calculator[/bold]")

                        yield Label("Operation:")
                        yield Select.from_values(["Relative Path", "Join Paths", "Expand User", "Resolve Absolute"], id="select-path-op", value="Relative Path")

                        # Dynamic inputs container
                        with Vertical(id="path-calc-inputs"):
                            yield Label("Target Path:", id="lbl-calc-1")
                            yield Input(placeholder="Target...", id="input-calc-1")
                            yield Label("Start Path (Base):", id="lbl-calc-2")
                            yield Input(placeholder="Start...", id="input-calc-2")

                        yield Button("Calculate", id="btn-path-calc", variant="primary")

                        yield Label("[bold]Result:[/bold]")
                        yield Static(id="lbl-path-result", classes="result-box")

                # GLOBBER
                with TabPane("Globber"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Glob Pattern Tester[/bold]")

                        yield Label("Base Directory:")
                        yield Input(value=str(self.project_dir), id="input-glob-base")

                        yield Label("Pattern:")
                        yield Input(placeholder="e.g. **/*.py", id="input-glob-pattern")

                        yield Button("Search", id="btn-path-glob", variant="warning")

                        yield Label("[bold]Matches:[/bold]")
                        yield RichLog(id="glob-results-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#path-inspect-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Property", "Value")

    @on(Button.Pressed, "#btn-path-inspect")
    def on_inspect(self) -> None:
        path_val = self.query_one("#path-inspect-input", Input).value
        if not path_val:
            self.notify("Path required.", severity="error")
            return

        info = self.manager.inspect_path(path_val)
        table = self.query_one("#path-inspect-table", DataTable)
        table.clear()

        if "error" in info:
            table.add_row("Error", f"[red]{info['error']}[/red]")
            return

        # Core props
        keys = ["parts", "name", "stem", "suffix", "parent", "absolute", "resolved"]
        for k in keys:
            if k in info:
                table.add_row(k.capitalize(), str(info[k]))

        # Flags
        flags = []
        if info.get("exists"): flags.append("Exists")
        if info.get("is_dir"): flags.append("Directory")
        if info.get("is_file"): flags.append("File")
        if info.get("is_symlink"): flags.append("Symlink")
        if info.get("is_absolute"): flags.append("Absolute")

        table.add_row("Type/Flags", ", ".join(flags))

        # Stats
        if info.get("exists"):
            table.add_row("Size", f"{info.get('size', 0)} bytes")
            table.add_row("Permissions", info.get("permissions_octal", "?"))
            table.add_row("Owner/Group", f"{info.get('owner')}/{info.get('group')}")

    @on(Select.Changed, "#select-path-op")
    def on_op_change(self, event: Select.Changed) -> None:
        op = event.value
        lbl1 = self.query_one("#lbl-calc-1", Label)
        inp1 = self.query_one("#input-calc-1", Input)
        lbl2 = self.query_one("#lbl-calc-2", Label)
        inp2 = self.query_one("#input-calc-2", Input)

        if op == "Relative Path":
            lbl1.update("Target Path:")
            lbl2.update("Start Path (Base):")
            lbl2.display = True
            inp2.display = True
        elif op == "Join Paths":
            lbl1.update("Path 1:")
            lbl2.update("Path 2 (comma separated for more):")
            lbl2.display = True
            inp2.display = True
        elif op == "Expand User":
            lbl1.update("Path (~/...):")
            lbl2.display = False
            inp2.display = False
        elif op == "Resolve Absolute":
            lbl1.update("Path:")
            lbl2.display = False
            inp2.display = False

    @on(Button.Pressed, "#btn-path-calc")
    def on_calc(self) -> None:
        op = self.query_one("#select-path-op", Select).value
        val1 = self.query_one("#input-calc-1", Input).value
        val2 = self.query_one("#input-calc-2", Input).value
        result_lbl = self.query_one("#lbl-path-result", Static)

        result = ""
        if op == "Relative Path":
            if not val1 or not val2:
                self.notify("Both inputs required.", severity="error")
                return
            result = self.manager.calculate_relative(val1, val2)

        elif op == "Join Paths":
            if not val1:
                self.notify("Path 1 required.", severity="error")
                return
            paths = [val1]
            if val2:
                # Basic comma split support
                extras = [p.strip() for p in val2.split(",")]
                paths.extend(extras)
            result = self.manager.join_paths(paths)

        elif op == "Expand User":
            if not val1:
                self.notify("Input required.", severity="error")
                return
            result = self.manager.expand_user(val1)

        elif op == "Resolve Absolute":
            if not val1:
                self.notify("Input required.", severity="error")
                return
            result = self.manager.resolve_path(val1)

        if result.startswith("Error"):
            result_lbl.update(f"[red]{result}[/red]")
        else:
            result_lbl.update(f"[green]{result}[/green]")

    @on(Button.Pressed, "#btn-path-glob")
    def on_glob(self) -> None:
        base = self.query_one("#input-glob-base", Input).value
        pattern = self.query_one("#input-glob-pattern", Input).value
        log = self.query_one("#glob-results-log", RichLog)

        if not base or not pattern:
            self.notify("Base and Pattern required.", severity="error")
            return

        log.clear()
        results = self.manager.glob_search(base, pattern)

        if not results:
            log.write("No matches.")
        else:
            for item in results:
                if item.startswith("Error"):
                    log.write(f"[red]{item}[/red]")
                else:
                    log.write(f"📄 {item}")
