"""
Alias Lab TUI
=============

Textual UI component for generating shell aliases.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import TabPane, Label, Input, Button, Select, RichLog
from textual import on

from shared.alias_lab import run_alias_lab_logic
import sys
import io


class AliasTab(TabPane):
    """A tab for Alias Lab operations."""

    def __init__(self):
        super().__init__("Alias Lab", id="tab-alias")

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-2"):
            yield Label("🔗 Shell Aliases Generator", classes="pane-title text-xl text-bold mb-2")

            with Container(classes="panel p-2 border mb-2"):
                with Horizontal(classes="mb-2"):
                    yield Label("Target Shell: ", classes="mt-1 mr-2")
                    yield Select(
                        [("Bash", "bash"), ("Zsh", "zsh"), ("Fish", "fish")],
                        value="bash",
                        id="alias-shell",
                        classes="w-1-3"
                    )

                with Horizontal(classes="mb-2"):
                    yield Label("Alias Prefix: ", classes="mt-1 mr-2")
                    yield Input(placeholder="e.g. agent-", id="alias-prefix", classes="w-1-3")

                yield Button("Generate Aliases", id="btn-generate-aliases", variant="primary")

            with Container(classes="panel p-2 border"):
                yield Label("Output:", classes="font-bold mb-1")
                yield RichLog(id="alias-log", wrap=True, highlight=True, markup=True, classes="h-full border")

    @on(Button.Pressed, "#btn-generate-aliases")
    async def on_generate_aliases(self, event: Button.Pressed) -> None:
        shell = self.query_one("#alias-shell", Select).value
        prefix = self.query_one("#alias-prefix", Input).value
        log = self.query_one("#alias-log", RichLog)

        log.clear()

        if shell == Select.BLANK or getattr(shell, "__class__", None).__name__ == "NoSelection" or not shell:
            self.notify("Please select a target shell.", severity="error")
            return

        # Use the known commands from main.py if possible, or replicate.
        from main import KNOWN_COMMANDS

        # We can capture stdout from run_alias_lab_logic
        import argparse
        args = argparse.Namespace(shell=shell, prefix=prefix)  # nosec B604

        old_stdout = sys.stdout
        sys.stdout = capture = io.StringIO()

        try:
            success = run_alias_lab_logic(args, KNOWN_COMMANDS)
        except Exception as e:
            sys.stdout = old_stdout
            self.notify(f"Error generating aliases: {e}", severity="error")
            return

        sys.stdout = old_stdout

        if success:
            log.write(capture.getvalue())
            self.notify("Aliases generated successfully.")
        else:
            self.notify("Failed to generate aliases.", severity="error")
