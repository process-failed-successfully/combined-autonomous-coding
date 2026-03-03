from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, Input, DataTable, RichLog
from textual import on
import asyncio

from shared.a11y import AccessibilityScanner


class A11yLabTab(Container):
    """Tab for interactive accessibility auditing."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Accessibility Scanner (A11y)[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Files:", classes="label")
                yield Input(placeholder="e.g. *.html, *.jsx (default: all web files)", id="inp-a11y-files")

                yield Label("Ignore:", classes="label")
                yield Input(placeholder="e.g. node_modules, dist", id="inp-a11y-ignore", value="node_modules*, dist*, build*, .git*")

                yield Button("Scan Now", id="btn-a11y-scan", variant="primary")

            with Horizontal():
                with Vertical(id="a11y-results-container", classes="stat-box"):
                    yield Label("[bold]Violations[/bold]")
                    yield DataTable(id="a11y-table")

                with Vertical(id="a11y-details-container", classes="stat-box"):
                    yield Label("[bold]Issue Details[/bold]")
                    yield RichLog(id="a11y-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#a11y-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("File", "Line", "Severity", "Message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-a11y-scan":
            await self.run_scan()

    async def run_scan(self) -> None:
        file_pattern = self.query_one("#inp-a11y-files", Input).value
        ignore_str = self.query_one("#inp-a11y-ignore", Input).value

        ignore_patterns = [p.strip() for p in ignore_str.split(",") if p.strip()] if ignore_str else []
        file_pattern = file_pattern if file_pattern else None

        self.notify("Scanning for accessibility issues...")
        self.query_one("#btn-a11y-scan").disabled = True

        table = self.query_one("#a11y-table", DataTable)
        table.clear()

        log = self.query_one("#a11y-log", RichLog)
        log.clear()

        # Run in thread
        try:
            scanner = await asyncio.to_thread(self._do_scan, file_pattern, ignore_patterns)

            if not scanner.violations:
                self.notify("No accessibility issues found! ✅")
                log.write("[bold green]All clear! No violations detected.[/bold green]")
            else:
                self.notify(f"Found {len(scanner.violations)} issues.", severity="warning")

                for i, v in enumerate(scanner.violations):
                    color = "red" if v.severity == "ERROR" else "yellow" if v.severity == "WARNING" else "blue"
                    table.add_row(
                        v.file,
                        str(v.lineno),
                        f"[{color}]{v.severity}[/{color}]",
                        v.message,
                        key=str(i)
                    )

            # Store for details view
            self.violations = scanner.violations

        except Exception as e:
            self.notify(f"Scan failed: {e}", severity="error")
            log.write(f"[bold red]Error:[/bold red] {e}")
        finally:
            self.query_one("#btn-a11y-scan").disabled = False

    def _do_scan(self, file_pattern, ignore_patterns):
        scanner = AccessibilityScanner(self.project_dir, file_pattern, ignore_patterns)
        scanner.scan()
        scanner.violations.sort(key=lambda x: (x.severity != "ERROR", x.file, x.lineno))
        return scanner

    @on(DataTable.RowSelected, "#a11y-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        if not hasattr(self, "violations"):
            return

        try:
            idx = int(event.row_key.value)
            v = self.violations[idx]

            log = self.query_one("#a11y-log", RichLog)
            log.clear()

            color = "red" if v.severity == "ERROR" else "yellow" if v.severity == "WARNING" else "blue"

            log.write(f"[bold]Rule ID:[/bold] {v.rule_id}")
            log.write(f"[bold]Severity:[/bold] [{color}]{v.severity}[/{color}]")
            log.write(f"[bold]File:[/bold] {v.file}")
            log.write(f"[bold]Line:[/bold] {v.lineno}")
            log.write("")
            log.write("[bold]Message:[/bold]")
            log.write(v.message)

        except Exception:
            pass
