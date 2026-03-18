from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, TextArea, RichLog
from shared.js_lab import JsLabManager

class JsLabTab(Container):
    """Tab for JavaScript Evaluation/Minification."""

    DEFAULT_CSS = """
    JsLabTab {
        layout: vertical;
        height: 100%;
    }

    .js-box {
        height: auto;
        border: solid $accent;
        padding: 1;
        margin: 1;
    }

    #js-input, #js-output {
        height: 1fr;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = JsLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]JavaScript Lab (Evaluator/Minifier)[/bold]", classes="welcome-text")

            # Input Section
            with Vertical(classes="js-box"):
                yield Label("Input JS:")
                yield TextArea(id="js-input", show_line_numbers=True, language="javascript")

            # Controls Section
            with Horizontal(classes="js-box"):
                yield Button("Run (Node.js)", id="btn-js-run", variant="primary")
                yield Button("Naive Minify", id="btn-js-minify", variant="success")
                yield Button("Clear", id="btn-js-clear", variant="error")

            # Output Section
            with Vertical(classes="js-box"):
                yield Label("Output/Console:")
                yield RichLog(id="js-output", wrap=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-js-run":
            await self.process(action="run")
        elif event.button.id == "btn-js-minify":
            await self.process(action="minify")
        elif event.button.id == "btn-js-clear":
            self.clear_content()

    async def process(self, action: str) -> None:
        text = self.query_one("#js-input", TextArea).text
        output_area = self.query_one("#js-output", RichLog)

        if not text:
            self.notify("Input is empty.", severity="warning")
            return

        output_area.clear()

        try:
            if action == "run":
                output_area.write("[bold]Evaluating with Node.js...[/bold]")
                import asyncio
                result = await asyncio.to_thread(self.manager.run_code, text)

                if result["stdout"]:
                    output_area.write("[bold green]STDOUT:[/bold green]")
                    output_area.write(result["stdout"])
                if result["stderr"]:
                    output_area.write("[bold red]STDERR:[/bold red]")
                    output_area.write(result["stderr"])
                if not result["stdout"] and not result["stderr"]:
                     output_area.write("[dim](No output)[/dim]")

                output_area.write(f"\n[dim]Exit Code: {result['exit_code']}[/dim]")
                self.notify("Execution Complete.")
            else:
                result = self.manager.minify(text)
                output_area.write("[bold green]Minified JS:[/bold green]")
                output_area.write(result["output"])
                self.notify("Done.")

        except Exception as e:
            output_area.write(f"[bold red]Error: {e}[/bold red]")
            self.notify(f"Exception: {e}", severity="error")

    def clear_content(self) -> None:
        self.query_one("#js-input", TextArea).text = ""
        self.query_one("#js-output", RichLog).clear()
        self.notify("Cleared.")
