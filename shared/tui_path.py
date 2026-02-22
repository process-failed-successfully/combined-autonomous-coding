from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, Button, DataTable, TabbedContent, TabPane, RichLog, Checkbox
from textual import on
from shared.path_lab import PathLabManager

class PathLabTab(Container):
    """Tab for Path Lab operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = PathLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Path Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # --- Inspector ---
                with TabPane("Inspector", id="path-tab-inspector"):
                    with Vertical(classes="stat-box"):
                        yield Label("Enter Path to Analyze:")
                        with Horizontal():
                            yield Input(placeholder="/path/to/file", id="path-insp-input")
                            yield Button("Analyze", id="btn-path-analyze", variant="primary")

                        yield DataTable(id="path-insp-table")

                # --- Calculator ---
                with TabPane("Calculator", id="path-tab-calc"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Relative Path Calculator[/bold]")
                        yield Input(placeholder="Target Path...", id="path-rel-target")
                        yield Input(placeholder="Start Path (default: current)...", id="path-rel-start")
                        yield Button("Calculate Relative", id="btn-path-rel", variant="warning")
                        yield Label("", id="lbl-path-rel-result")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Join Paths[/bold]")
                        yield Input(placeholder="Base Path...", id="path-join-base")
                        yield Input(placeholder="Parts (comma separated)...", id="path-join-parts")
                        yield Button("Join", id="btn-path-join", variant="success")
                        yield Label("", id="lbl-path-join-result")

                # --- Globber ---
                with TabPane("Globber", id="path-tab-glob"):
                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Glob Tester[/bold]")
                        yield Input(placeholder="Root Directory (default: current)...", id="path-glob-root")
                        yield Input(placeholder="Pattern (e.g. *.py)...", id="path-glob-pattern")
                        yield Checkbox("Recursive (rglob)", id="chk-path-glob-rec")
                        yield Button("Run Glob", id="btn-path-glob", variant="primary")

                        yield Label("Matches:")
                        yield RichLog(id="path-glob-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#path-insp-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Property", "Value")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-path-analyze":
            self.analyze_path()
        elif event.button.id == "btn-path-rel":
            self.calculate_relative()
        elif event.button.id == "btn-path-join":
            self.join_paths()
        elif event.button.id == "btn-path-glob":
            self.run_glob()

    def analyze_path(self) -> None:
        path_str = self.query_one("#path-insp-input", Input).value
        if not path_str:
            self.notify("Please enter a path.", severity="error")
            return

        info = self.manager.analyze_path(path_str)

        table = self.query_one("#path-insp-table", DataTable)
        table.clear()

        # Core props
        table.add_row("Original", info["original"])
        table.add_row("Resolved", info["resolved"] or "N/A")
        table.add_row("Exists", str(info["exists"]))
        table.add_row("Absolute", info["absolute"])
        table.add_row("Is Absolute", str(info["is_absolute"]))

        # Parts
        table.add_row("Anchor", info["anchor"] or "(None)")
        table.add_row("Parent", info["parent"])
        table.add_row("Name", info["name"])
        table.add_row("Stem", info["stem"])
        table.add_row("Suffix", info["suffix"])

        # Type
        if info["exists"]:
            p_type = []
            if info["is_file"]: p_type.append("File")
            if info["is_dir"]: p_type.append("Directory")
            if info["is_symlink"]: p_type.append("Symlink")
            table.add_row("Type", ", ".join(p_type))

            if info["stat"] and isinstance(info["stat"], dict):
                s = info["stat"]
                table.add_row("Size", f"{s['size']} bytes")
                table.add_row("Mode", s['mode'])
                table.add_row("UID/GID", f"{s['uid']}/{s['gid']}")

    def calculate_relative(self) -> None:
        target = self.query_one("#path-rel-target", Input).value
        start = self.query_one("#path-rel-start", Input).value or "."

        if not target:
            self.notify("Target required.", severity="error")
            return

        res = self.manager.calculate_relative(target, start)
        lbl = self.query_one("#lbl-path-rel-result", Label)

        if res["success"]:
            lbl.update(f"[green]Result: {res['result']}[/green]")
        else:
            lbl.update(f"[red]Error: {res['error']}[/red]")

    def join_paths(self) -> None:
        base = self.query_one("#path-join-base", Input).value
        parts_str = self.query_one("#path-join-parts", Input).value

        if not base:
            self.notify("Base path required.", severity="error")
            return

        parts = [p.strip() for p in parts_str.split(",") if p.strip()]

        result = self.manager.join_paths(base, parts)
        self.query_one("#lbl-path-join-result", Label).update(f"[green]Result: {result}[/green]")

    def run_glob(self) -> None:
        root = self.query_one("#path-glob-root", Input).value or "."
        pattern = self.query_one("#path-glob-pattern", Input).value
        recursive = self.query_one("#chk-path-glob-rec", Checkbox).value

        if not pattern:
            self.notify("Pattern required.", severity="error")
            return

        log = self.query_one("#path-glob-log", RichLog)
        log.clear()
        log.write(f"Globbing '{pattern}' in '{root}' (Recursive: {recursive})...")

        matches = self.manager.glob_path(root, pattern, recursive)

        if not matches:
            log.write("[yellow]No matches found.[/yellow]")
        else:
            log.write(f"[green]Found {len(matches)} matches:[/green]")
            for m in matches:
                log.write(f"  - {m}")
