from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Select, Input, Button, RichLog
from textual import on
from shared.alias_lab import run_alias_lab_logic
import argparse
from typing import List

class AliasLabTab(Container):
    """Tab for generating shell aliases for all known CLI commands."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Alias Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Target Shell:")
                    yield Select.from_values(["bash", "zsh", "fish"], id="alias-shell-select", value="bash")
                with Vertical():
                    yield Label("Alias Prefix:")
                    yield Input(placeholder="e.g. agent-", id="alias-prefix-input")

            with Horizontal(classes="stat-box"):
                yield Button("Generate Aliases", id="btn-generate-aliases", variant="primary")

            yield Label("[bold]Generated Aliases[/bold]")
            yield RichLog(id="alias-output-log", wrap=False, highlight=True, markup=False)

    @on(Button.Pressed, "#btn-generate-aliases")
    def on_generate_aliases(self) -> None:
        shell_val = self.query_one("#alias-shell-select", Select).value or "bash"
        prefix_val = self.query_one("#alias-prefix-input", Input).value

        # Mock the args for the CLI logic
        args = argparse.Namespace(shell=shell_val, prefix=prefix_val)  # nosec B604

        # Import KNOWN_COMMANDS lazily from main.py
        try:
            import main
            known_commands = getattr(main, "KNOWN_COMMANDS", [])
        except ImportError:
            known_commands = []

        if not known_commands:
            self.notify("Error: Could not load KNOWN_COMMANDS from main.py", severity="error")
            return

        # Redirect stdout to capture the output of run_alias_lab_logic
        import io
        import contextlib

        output_capture = io.StringIO()
        with contextlib.redirect_stdout(output_capture):
            success = run_alias_lab_logic(args, known_commands)

        log = self.query_one("#alias-output-log", RichLog)
        log.clear()

        if success:
            log.write(output_capture.getvalue())
            self.notify("Aliases generated successfully.")
        else:
            log.write("Failed to generate aliases.")
            self.notify("Error generating aliases.", severity="error")
