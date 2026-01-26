from textual.app import ComposeResult
from textual.widgets import Label, Button, DataTable, RichLog
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from pathlib import Path
import asyncio
import sys

from shared.impact import ImpactAnalyzer

class ImpactTab(Container):
    """Tab for Impact Analysis."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.analyzer = ImpactAnalyzer(project_dir)
        self.impacted_tests = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Impact Analysis[/bold]", classes="welcome-text")

            # Top Controls
            with Horizontal(classes="stat-box"):
                yield Button("Analyze Impact", id="btn-impact-analyze", variant="primary")
                yield Button("Run Suggested Tests", id="btn-impact-run-tests", variant="warning", disabled=True)
                yield Label("", id="impact-status-lbl")

            # Lists
            with Horizontal():
                # Changed Files
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Changed Files[/bold]")
                    yield DataTable(id="impact-changed-table")

                # Impacted Source
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Impacted Source[/bold]")
                    yield DataTable(id="impact-source-table")

                # Impacted Tests
                with Vertical(classes="stat-box"):
                    yield Label("[bold]Suggested Tests[/bold]")
                    yield DataTable(id="impact-tests-table")

            # Output
            with VerticalScroll(classes="stat-box"):
                yield Label("[bold]Test Output[/bold]")
                yield RichLog(id="impact-test-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        # Init Tables
        for table_id in ["#impact-changed-table", "#impact-source-table", "#impact-tests-table"]:
            table = self.query_one(table_id, DataTable)
            table.cursor_type = "row"
            table.add_columns("File")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-impact-analyze":
            await self.run_analysis()
        elif event.button.id == "btn-impact-run-tests":
            await self.run_tests()

    async def run_analysis(self) -> None:
        self.query_one("#impact-status-lbl").update("Analyzing dependencies...")
        self.query_one("#btn-impact-run-tests").disabled = True

        # Clear tables
        for table_id in ["#impact-changed-table", "#impact-source-table", "#impact-tests-table"]:
            self.query_one(table_id, DataTable).clear()

        try:
            # Run in thread
            result = await asyncio.to_thread(self._analyze)

            changed, source, tests = result

            # Populate tables
            self._populate_table("#impact-changed-table", changed)
            self._populate_table("#impact-source-table", source)
            self._populate_table("#impact-tests-table", tests)

            self.impacted_tests = sorted(list(tests))

            count_msg = f"Found {len(changed)} changed, {len(source)} source impacted, {len(tests)} tests."
            self.query_one("#impact-status-lbl").update(count_msg)

            if self.impacted_tests:
                self.query_one("#btn-impact-run-tests").disabled = False

            self.notify("Analysis complete.")

        except Exception as e:
            self.query_one("#impact-status-lbl").update(f"Error: {e}")
            self.notify(f"Analysis failed: {e}", severity="error")

    def _analyze(self):
        self.analyzer.build_graph()
        changed = self.analyzer.get_changed_files()
        source, tests = self.analyzer.find_impacted_files(changed)
        # Filter changed out of source for clarity (same as CLI)
        source = source - set(changed)
        return changed, source, tests

    def _populate_table(self, table_id: str, items: list | set):
        table = self.query_one(table_id, DataTable)
        for item in sorted(list(items)):
            table.add_row(item)

    async def run_tests(self) -> None:
        if not self.impacted_tests:
            return

        log = self.query_one("#impact-test-log", RichLog)
        log.clear()
        log.write(f"Running {len(self.impacted_tests)} tests...")
        self.query_one("#impact-status-lbl").update("Running tests...")

        cmd = [sys.executable, "-m", "pytest"] + self.impacted_tests

        import subprocess

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.project_dir)
            )

            async def read_stream(stream, callback):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    callback(line.decode().rstrip())

            await asyncio.gather(
                read_stream(process.stdout, log.write),
                read_stream(process.stderr, lambda l: log.write(f"[red]{l}[/red]"))
            )

            await process.wait()

            if process.returncode == 0:
                log.write("\n[bold green]Tests Passed![/bold green]")
                self.query_one("#impact-status-lbl").update("Tests Passed.")
            else:
                log.write(f"\n[bold red]Tests Failed (Exit Code: {process.returncode})[/bold red]")
                self.query_one("#impact-status-lbl").update("Tests Failed.")

        except Exception as e:
            log.write(f"[bold red]Execution Error:[/bold red] {e}")
            self.query_one("#impact-status-lbl").update("Execution Error.")
