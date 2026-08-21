import asyncio
import shlex
import re
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, Select, Markdown
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on, work

from shared.bisect import analyze_commit
from shared.git import get_git_log

class BisectTab(Container):
    """Tab for automated git bisect operations."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.bisect_running = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Smart Bisect Lab[/bold]", classes="welcome-text")

            # Configuration
            with Vertical(classes="stat-box", id="bisect-config"):
                yield Label("[bold]Configuration[/bold]")

                with Horizontal():
                    with Vertical():
                        yield Label("Bad Commit (Newest):")
                        yield Input(placeholder="HEAD", id="bisect-bad", value="HEAD")
                    with Vertical():
                        yield Label("Good Commit (Oldest):")
                        yield Select([], id="bisect-good-select", prompt="Select recent...")
                        yield Input(placeholder="Or type hash manually...", id="bisect-good-manual")

                yield Label("Test Command (returns 0 for good, non-0 for bad):")
                yield Input(placeholder="python run_tests.py", id="bisect-command")

                with Horizontal():
                    yield Select.from_values(["gemini", "cursor", "local"], id="bisect-agent", value="gemini")
                    yield Button("Start Bisect", id="btn-bisect-start", variant="primary")
                    yield Button("Reset Git Bisect", id="btn-bisect-reset", variant="warning")

            # Progress
            with Vertical(classes="stat-box", id="bisect-progress"):
                with Horizontal():
                    yield Label("[bold]Progress Log[/bold]")
                    yield Label("Idle", id="bisect-status")
                yield RichLog(id="bisect-log", wrap=True, highlight=True, markup=True)

            # Analysis
            with VerticalScroll(classes="stat-box", id="bisect-analysis"):
                yield Label("[bold]Culprit Analysis[/bold]")
                yield Markdown("Run bisect to see analysis.", id="bisect-markdown")

    def on_mount(self) -> None:
        self.load_commits()

    def load_commits(self) -> None:
        # Load recent commits for "Good Commit" selection
        logs = get_git_log(self.project_dir, limit=50)
        options = []
        for log in logs:
            label = f"{log['hash'][:7]} - {log['message'][:40]} ({log['date']})"
            options.append((label, log['hash']))

        select = self.query_one("#bisect-good-select", Select)
        select.set_options(options)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-bisect-start":
            self.start_bisect()
        elif event.button.id == "btn-bisect-reset":
            await self.reset_bisect()

    async def reset_bisect(self) -> None:
        log = self.query_one("#bisect-log", RichLog)
        log.write("[yellow]Resetting git bisect...[/yellow]")

        proc = await asyncio.create_subprocess_exec(
            "git", "bisect", "reset",
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        log.write("[green]Reset complete.[/green]")
        self.query_one("#bisect-status", Label).update("Idle")
        self.bisect_running = False
        self.query_one("#btn-bisect-start").disabled = False

    @work
    async def start_bisect(self) -> None:
        if self.bisect_running:
            return

        bad = self.query_one("#bisect-bad", Input).value or "HEAD"
        good_select = self.query_one("#bisect-good-select", Select).value
        good_manual = self.query_one("#bisect-good-manual", Input).value
        good = good_manual if good_manual else good_select

        cmd = self.query_one("#bisect-command", Input).value

        if not good:
            self.notify("Please select or enter a good commit.", severity="error")
            return
        if not cmd:
            self.notify("Please enter a test command.", severity="error")
            return

        self.bisect_running = True
        self.query_one("#btn-bisect-start").disabled = True

        log = self.query_one("#bisect-log", RichLog)
        log.clear()
        status_lbl = self.query_one("#bisect-status", Label)

        try:
            # 1. Start
            log.write(f"[bold]Starting bisect:[/bold] Bad={bad}, Good={good}")
            success = await self._run_git_cmd(["git", "bisect", "start", bad, good], log)
            if not success:
                log.write("[bold red]Failed to start bisect. Check logs above.[/bold red]")
                return

            # 2. Run
            log.write(f"[bold]Running automated bisect with command:[/bold] {cmd}")
            status_lbl.update("Running...")

            # We use subprocess directly to stream output
            full_cmd = ["git", "bisect", "run"] + shlex.split(cmd)

            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                cwd=self.project_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            bad_commit_hash = None

            while True:
                line_bytes = await process.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode('utf-8', errors='replace').strip()
                if line:
                    log.write(line)
                    # Parse progress
                    if "revisions left" in line:
                        status_lbl.update(f"[cyan]{line}[/cyan]")

                    # Check for culprit
                    # "b01d... is the first (?:'bad'|bad) commit"
                    match = re.search(r"^([a-f0-9]+) is the first (?:'bad'|bad) commit", line)
                    if match:
                        bad_commit_hash = match.group(1)
                        log.write(f"\n[bold green]FOUND CULPRIT: {bad_commit_hash}[/bold green]")

            await process.wait()

            if process.returncode != 0:
                log.write(f"[bold red]Bisect failed with exit code {process.returncode}[/bold red]")

            # 3. Analyze if found
            if bad_commit_hash:
                await self.analyze_culprit(bad_commit_hash, cmd)
            else:
                log.write("[bold yellow]Could not identify the bad commit.[/bold yellow]")

        except Exception as e:
            log.write(f"[bold red]Error: {e}[/bold red]")
        finally:
            # Cleanup
            await self._run_git_cmd(["git", "bisect", "reset"], log)
            self.bisect_running = False
            self.query_one("#btn-bisect-start").disabled = False
            status_lbl.update("Idle (Reset complete)")

    async def _run_git_cmd(self, cmd: list[str], log: RichLog) -> bool:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.project_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if stdout: log.write(stdout.decode().strip())
        if stderr: log.write(f"[red]{stderr.decode().strip()}[/red]")
        return proc.returncode == 0

    async def analyze_culprit(self, commit_hash: str, cmd: str) -> None:
        md_view = self.query_one("#bisect-markdown", Markdown)
        md_view.update("Analyzing culprit with AI... please wait.")

        agent_type = self.query_one("#bisect-agent", Select).value or "gemini"

        try:
            analysis = await analyze_commit(
                self.project_dir,
                commit_hash,
                f"The command '{cmd}' failed on this commit.",
                agent_type=agent_type
            )
            md_view.update(analysis)
        except Exception as e:
            md_view.update(f"Error during analysis: {e}")
