from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Label, Input, RichLog, TabbedContent, TabPane, DataTable
from textual import on
from pathlib import Path
import asyncio

from shared.fuzz_lab import FuzzLabManager

class FuzzLabTab(Container):
    """Tab for Fuzz Lab operations (CLI and Function fuzzing)."""

    def __init__(self, project_dir: Path = Path("."), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_dir = project_dir
        self.manager = FuzzLabManager(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Fuzz Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # CLI Fuzzing Pane
                with TabPane("CLI Fuzzing", id="fuzz-cli-pane"):
                    with Horizontal(classes="stat-box"):
                        yield Label("Command:")
                        yield Input(id="fuzz-cli-target", placeholder="e.g., python3 app.py")
                        yield Label("Count:")
                        yield Input(id="fuzz-cli-count", value="10", type="integer")
                        yield Label("Timeout (s):")
                        yield Input(id="fuzz-cli-timeout", value="5", type="integer")
                    with Horizontal(classes="action-buttons"):
                        yield Button("Fuzz CLI", id="btn-fuzz-cli", variant="primary")
                    with VerticalScroll(classes="stat-box"):
                        yield Label("[bold]Crashes/Errors[/bold]")
                        yield DataTable(id="fuzz-cli-table")
                        yield RichLog(id="fuzz-cli-log", markup=True, wrap=True)

                # Function Fuzzing Pane
                with TabPane("Function Fuzzing", id="fuzz-func-pane"):
                    with Horizontal(classes="stat-box"):
                        yield Label("Target (file.py:func_name):")
                        yield Input(id="fuzz-func-target", placeholder="e.g., shared/utils.py:my_func")
                        yield Label("Count:")
                        yield Input(id="fuzz-func-count", value="10", type="integer")
                    with Horizontal(classes="action-buttons"):
                        yield Button("Fuzz Function", id="btn-fuzz-func", variant="warning")
                    with VerticalScroll(classes="stat-box"):
                        yield Label("[bold]Exceptions[/bold]")
                        yield DataTable(id="fuzz-func-table")
                        yield RichLog(id="fuzz-func-log", markup=True, wrap=True)

    def on_mount(self) -> None:
        # Initialize CLI DataTable
        cli_table = self.query_one("#fuzz-cli-table", DataTable)
        cli_table.cursor_type = "row"
        cli_table.add_columns("Iter", "Type", "Input Preview", "Code")

        # Initialize Function DataTable
        func_table = self.query_one("#fuzz-func-table", DataTable)
        func_table.cursor_type = "row"
        func_table.add_columns("Iter", "Type", "Args", "Error")

    @on(Button.Pressed, "#btn-fuzz-cli")
    async def on_fuzz_cli(self) -> None:
        target = self.query_one("#fuzz-cli-target", Input).value
        count_str = self.query_one("#fuzz-cli-count", Input).value
        timeout_str = self.query_one("#fuzz-cli-timeout", Input).value

        log = self.query_one("#fuzz-cli-log", RichLog)
        table = self.query_one("#fuzz-cli-table", DataTable)
        btn = self.query_one("#btn-fuzz-cli", Button)

        if not target:
            self.notify("CLI target is required.", severity="error")
            return

        count = int(count_str) if count_str else 10
        timeout = int(timeout_str) if timeout_str else 5

        log.clear()
        table.clear()
        log.write(f"[bold]Starting CLI fuzzing for '{target}' ({count} iterations)...[/bold]")
        self.notify("Fuzzing CLI...")
        btn.disabled = True

        try:
            # Run fuzzing in a separate thread so it doesn't block the UI
            crashes = await asyncio.to_thread(
                self.manager.fuzz_cli, target, count=count, timeout=timeout
            )

            if not crashes:
                log.write("[bold green]✅ Fuzzing complete. No crashes detected.[/bold green]")
                self.notify("Fuzzing complete. No issues found.")
            else:
                log.write(f"[bold red]❌ Found {len(crashes)} issues.[/bold red]")
                for c in crashes:
                    table.add_row(
                        str(c["iteration"]),
                        c["type"],
                        c["input_preview"].replace("\n", "\\n"),
                        str(c["return_code"])
                    )
                self.notify(f"Found {len(crashes)} issues.", severity="warning")
        except Exception as e:
            log.write(f"[bold red]Execution Error: {e}[/bold red]")
            self.notify("Fuzzing error", severity="error")
        finally:
            btn.disabled = False

    @on(Button.Pressed, "#btn-fuzz-func")
    async def on_fuzz_func(self) -> None:
        target = self.query_one("#fuzz-func-target", Input).value
        count_str = self.query_one("#fuzz-func-count", Input).value

        log = self.query_one("#fuzz-func-log", RichLog)
        table = self.query_one("#fuzz-func-table", DataTable)
        btn = self.query_one("#btn-fuzz-func", Button)

        if not target or ":" not in target:
            self.notify("Target must be in 'file.py:function_name' format.", severity="error")
            return

        count = int(count_str) if count_str else 10
        file_path, func_name = target.split(":", 1)

        log.clear()
        table.clear()
        log.write(f"[bold]Starting function fuzzing for '{func_name}' in '{file_path}' ({count} iterations)...[/bold]")
        self.notify("Fuzzing function...")
        btn.disabled = True

        try:
            # Run fuzzing in a separate thread so it doesn't block the UI
            failures = await asyncio.to_thread(
                self.manager.fuzz_function, file_path, func_name, count=count
            )

            if not failures:
                log.write("[bold green]✅ Fuzzing complete. No unhandled exceptions detected.[/bold green]")
                self.notify("Fuzzing complete. No issues found.")
            else:
                log.write(f"[bold red]❌ Found {len(failures)} exceptions.[/bold red]")
                for f in failures:
                    args_str = f"{f['args']}, {f['kwargs']}"
                    table.add_row(
                        str(f["iteration"]),
                        f["type"],
                        args_str[:50],
                        f["error"][:80]
                    )
                self.notify(f"Found {len(failures)} exceptions.", severity="warning")
        except Exception as e:
            log.write(f"[bold red]Execution Error: {e}[/bold red]")
            self.notify("Fuzzing error", severity="error")
        finally:
            btn.disabled = False
