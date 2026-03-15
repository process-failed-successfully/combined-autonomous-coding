from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, Select, TabbedContent, TabPane, TextArea, DataTable, Checkbox, RichLog
from shared.hash_lab import HashLabManager
import asyncio


class HashLabTab(Container):
    """Tab for Hash operations (String, File, Dir, Checksum)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = HashLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Hash Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # String Hashing
                with TabPane("String"):
                    with Vertical(classes="stat-box"):
                        yield Label("Input Text:")
                        yield TextArea(id="hash-string-input")
                        with Horizontal():
                            yield Label("Algorithm:", classes="label")
                            yield Select.from_values(["md5", "sha1", "sha256", "sha512"], id="hash-string-algo", value="sha256")
                            yield Input(placeholder="Optional HMAC Key", id="hash-string-hmac")
                            yield Button("Calculate", id="btn-hash-string", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Result[/bold]")
                        yield TextArea(id="hash-string-output", read_only=True)

                # File Hashing
                with TabPane("File"):
                    with Vertical(classes="stat-box"):
                        yield Label("File Path:")
                        yield Input(placeholder="path/to/file", id="hash-file-input")
                        with Horizontal():
                            yield Label("Algorithm:", classes="label")
                            yield Select.from_values(["md5", "sha1", "sha256", "sha512"], id="hash-file-algo", value="sha256")
                            yield Input(placeholder="Optional HMAC Key", id="hash-file-hmac")
                            yield Button("Calculate", id="btn-hash-file", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Result[/bold]")
                        yield TextArea(id="hash-file-output", read_only=True)

                # Directory Hashing
                with TabPane("Directory"):
                    with Vertical(classes="stat-box"):
                        yield Label("Directory Path:")
                        yield Input(placeholder="path/to/dir", id="hash-dir-input")
                        with Horizontal():
                            yield Checkbox("Recursive", id="hash-dir-recursive")
                            yield Label("Algorithm:", classes="label")
                            yield Select.from_values(["md5", "sha1", "sha256", "sha512"], id="hash-dir-algo", value="sha256")
                            yield Input(placeholder="Optional HMAC Key", id="hash-dir-hmac")
                            yield Button("Calculate", id="btn-hash-dir", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Results[/bold]")
                        yield DataTable(id="hash-dir-table")

                # Compare Files
                with TabPane("Compare"):
                    with Vertical(classes="stat-box"):
                        yield Label("File 1:")
                        yield Input(placeholder="path/to/file1", id="hash-compare-1")
                        yield Label("File 2:")
                        yield Input(placeholder="path/to/file2", id="hash-compare-2")
                        with Horizontal():
                            yield Label("Algorithm:", classes="label")
                            yield Select.from_values(["md5", "sha1", "sha256", "sha512"], id="hash-compare-algo", value="sha256")
                            yield Button("Compare", id="btn-hash-compare", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Result[/bold]")
                        yield RichLog(id="hash-compare-log", wrap=True, highlight=True, markup=True)

                # Checksum Verification
                with TabPane("Checksums"):
                    with Vertical(classes="stat-box"):
                        yield Label("Checksum File:")
                        yield Input(placeholder="path/to/checksums.txt", id="hash-sum-file")
                        yield Label("Root Directory (Optional):")
                        yield Input(placeholder="path/to/root", id="hash-sum-root")
                        with Horizontal():
                            yield Label("Algorithm:", classes="label")
                            yield Select.from_values(["md5", "sha1", "sha256", "sha512"], id="hash-sum-algo", value="sha256")
                            yield Button("Verify", id="btn-hash-verify", variant="success")

                    with Vertical(classes="stat-box"):
                        yield Label("[bold]Verification Log[/bold]")
                        yield RichLog(id="hash-sum-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#hash-dir-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("File", "Hash")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-hash-string":
            self.hash_string()
        elif event.button.id == "btn-hash-file":
            await self.hash_file()
        elif event.button.id == "btn-hash-dir":
            await self.hash_dir()
        elif event.button.id == "btn-hash-compare":
            await self.compare_files()
        elif event.button.id == "btn-hash-verify":
            await self.verify_checksums()

    def hash_string(self) -> None:
        text = self.query_one("#hash-string-input", TextArea).text
        algo = self.query_one("#hash-string-algo", Select).value or "sha256"
        hmac_key = self.query_one("#hash-string-hmac", Input).value
        out = self.query_one("#hash-string-output", TextArea)

        if not text:
            self.notify("Input required.", severity="error")
            return

        try:
            res = self.manager.hash_string(text, str(algo), hmac_key)
            out.text = res
            self.notify("Hash calculated.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def hash_file(self) -> None:
        path_str = self.query_one("#hash-file-input", Input).value
        algo = self.query_one("#hash-file-algo", Select).value or "sha256"
        hmac_key = self.query_one("#hash-file-hmac", Input).value
        out = self.query_one("#hash-file-output", TextArea)

        if not path_str:
            self.notify("File path required.", severity="error")
            return

        path = self.project_dir / path_str.lstrip("/")

        try:
            # Run in thread
            res = await asyncio.to_thread(self.manager.hash_file, path, str(algo), hmac_key)
            out.text = res
            self.notify("File hashed.")
        except Exception as e:
            out.text = f"Error: {e}"
            self.notify(f"Error: {e}", severity="error")

    async def hash_dir(self) -> None:
        path_str = self.query_one("#hash-dir-input", Input).value
        algo = self.query_one("#hash-dir-algo", Select).value or "sha256"
        hmac_key = self.query_one("#hash-dir-hmac", Input).value
        recursive = self.query_one("#hash-dir-recursive", Checkbox).value
        table = self.query_one("#hash-dir-table", DataTable)

        if not path_str:
            self.notify("Directory path required.", severity="error")
            return

        path = self.project_dir / path_str.lstrip("/")
        table.clear()
        self.notify("Hashing directory...")

        try:
            results = await asyncio.to_thread(self.manager.hash_dir, path, str(algo), recursive, hmac_key)

            for f, h in sorted(results.items()):
                # Try to make path relative for display
                try:
                    display_path = Path(f).relative_to(path)
                except ValueError:
                    display_path = f
                table.add_row(str(display_path), h)

            self.notify(f"Hashed {len(results)} files.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")

    async def compare_files(self) -> None:
        p1_str = self.query_one("#hash-compare-1", Input).value
        p2_str = self.query_one("#hash-compare-2", Input).value
        algo = self.query_one("#hash-compare-algo", Select).value or "sha256"
        log = self.query_one("#hash-compare-log", RichLog)

        if not p1_str or not p2_str:
            self.notify("Two file paths required.", severity="error")
            return

        p1 = self.project_dir / p1_str.lstrip("/")
        p2 = self.project_dir / p2_str.lstrip("/")

        log.clear()
        self.notify("Comparing...")

        try:
            res = await asyncio.to_thread(self.manager.compare_files, p1, p2, str(algo))

            if res["match"]:
                log.write("[bold green]✅ FILES MATCH[/bold green]")
            else:
                log.write("[bold red]❌ FILES DO NOT MATCH[/bold red]")

            log.write(f"File 1: {res['hash1']}")
            log.write(f"File 2: {res['hash2']}")

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify("Comparison failed.", severity="error")

    async def verify_checksums(self) -> None:
        sum_file_str = self.query_one("#hash-sum-file", Input).value
        root_str = self.query_one("#hash-sum-root", Input).value
        algo = self.query_one("#hash-sum-algo", Select).value or "sha256"
        log = self.query_one("#hash-sum-log", RichLog)

        if not sum_file_str:
            self.notify("Checksum file required.", severity="error")
            return

        sum_file = self.project_dir / sum_file_str.lstrip("/")
        root = (self.project_dir / root_str.lstrip("/")) if root_str else None

        log.clear()
        self.notify("Verifying...")

        try:
            res = await asyncio.to_thread(self.manager.verify_checksums, sum_file, str(algo), root)

            passed = len(res["passed"])
            failed = len(res["failed"])
            missing = len(res["missing"])
            errors = len(res["errors"])

            log.write(f"[bold]Summary:[/bold] Passed: [green]{passed}[/green], Failed: [red]{failed}[/red], Missing: [yellow]{missing}[/yellow], Errors: [red]{errors}[/red]")

            if failed > 0:
                log.write("\n[bold red]Failures:[/bold red]")
                for f in res["failed"]:
                    log.write(f"  {f['file']} (Expected: {f['expected']}, Got: {f['actual']})")

            if missing > 0:
                log.write("\n[bold yellow]Missing Files:[/bold yellow]")
                for f in res["missing"]:
                    log.write(f"  {f}")

            if errors > 0:
                log.write("\n[bold red]Errors:[/bold red]")
                for e in res["errors"]:
                    log.write(f"  {e}")

            if failed == 0 and missing == 0 and errors == 0:
                log.write("\n[bold green]All checks passed![/bold green]")

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify("Verification failed.", severity="error")
