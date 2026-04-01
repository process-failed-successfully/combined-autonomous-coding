import hashlib
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, Input, TextArea, RichLog
from textual import on

from shared.hash_validator_lab import HashValidatorManager


class HashValidatorLabTab(Container):
    """Tab for Hash Validator operations."""

    def __init__(self, project_dir: Path = Path("."), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_dir = project_dir
        self.manager = HashValidatorManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Hash Validator Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="action-buttons"):
                yield Button("Detect Type", id="btn-hash-detect", variant="primary")
                yield Button("Verify", id="btn-hash-verify", variant="success")
                yield Button("Clear", id="btn-hash-clear", variant="error")

            with Horizontal(classes="config-row"):
                yield Label("Expected Hash:")
                yield Input(placeholder="Enter hex hash here...", id="hash-expected-input")

                yield Label("Algorithm (Optional):")
                yield Input(placeholder="e.g. sha256", id="hash-algo-input")

            with Horizontal(classes="editor-row"):
                with Vertical():
                    yield Label("Input Text:")
                    yield TextArea(
                        id="hash-text-input",
                        text=""
                    )
            yield RichLog(id="hash-validator-log", markup=True, wrap=True, highlight=False, classes="hash-validator-log")

    @on(Button.Pressed, "#btn-hash-detect")
    def on_detect(self) -> None:
        log = self.query_one("#hash-validator-log", RichLog)
        hash_val = self.query_one("#hash-expected-input", Input).value.strip()

        log.clear()
        if not hash_val:
            log.write("[bold red]Error: No hash provided for detection.[/bold red]")
            return

        algos = self.manager.detect_hash_type(hash_val)
        if algos:
            log.write(f"[bold blue]Detected possible algorithms for length {len(hash_val)}:[/bold blue]")
            for algo in algos:
                log.write(f"  - {algo}")
        else:
            log.write("[bold red]Could not detect any standard hash algorithm for this input length.[/bold red]")

    @on(Button.Pressed, "#btn-hash-verify")
    def on_verify(self) -> None:
        log = self.query_one("#hash-validator-log", RichLog)
        hash_val = self.query_one("#hash-expected-input", Input).value.strip()
        text_val = self.query_one("#hash-text-input", TextArea).text
        algo_val = self.query_one("#hash-algo-input", Input).value.strip()

        log.clear()
        if not hash_val:
            log.write("[bold red]Error: No expected hash provided for verification.[/bold red]")
            return

        if not text_val:
            log.write("[bold red]Error: No input text provided for verification.[/bold red]")
            return

        # Let the manager attempt to verify
        algo = algo_val if algo_val else None

        # Check lengths first before computing
        algos_to_try = [algo.lower()] if algo else self.manager.detect_hash_type(hash_val)

        if not algos_to_try:
            log.write("[bold red]Error: Could not detect hash algorithm, and none was provided.[/bold red]")
            return

        success = False
        input_bytes = text_val.encode('utf-8')

        for a in algos_to_try:
            try:
                h = hashlib.new(a)
                h.update(input_bytes)
                if h.hexdigest() == hash_val.lower():
                    log.write(f"[bold green]✅ Match found! Algorithm used: {a}[/bold green]")
                    success = True
                    break
            except ValueError:
                # Unsupported algo
                continue

        if not success:
            log.write("[bold red]❌ No match found.[/bold red]")
            log.write(f"[dim]Tried algorithms: {', '.join(algos_to_try)}[/dim]")

    @on(Button.Pressed, "#btn-hash-clear")
    def on_clear(self) -> None:
        self.query_one("#hash-expected-input", Input).value = ""
        self.query_one("#hash-text-input", TextArea).text = ""
        self.query_one("#hash-algo-input", Input).value = ""
        self.query_one("#hash-validator-log", RichLog).clear()
