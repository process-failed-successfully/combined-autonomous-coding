from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, Static
from textual.containers import Container, Horizontal, Vertical
from shared.calc_lab import CalcLabManager


class CalcLabTab(Container):
    """Tab for Calculator Lab operations."""

    DEFAULT_CSS = """
    CalcLabTab {
        layout: vertical;
        height: 100%;
    }

    .calc-box {
        background: $boost;
        padding: 1;
        margin-bottom: 1;
    }

    #input-calc-eval {
        width: 1fr;
    }

    #btn-calc-eval {
        margin-left: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = CalcLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Calculator Lab[/bold]", classes="welcome-text")

            with Vertical(classes="calc-box"):
                yield Label("Expression:")
                with Horizontal():
                    yield Input(placeholder="e.g. 2 + 2 * 4, x = 10, 0xFF + 1, ~0...", id="input-calc-eval")
                    yield Button("Calculate", id="btn-calc-eval", variant="primary")
                    yield Button("Clear Log", id="btn-calc-clear", variant="error")

                yield Label("[bold]Variables[/bold]")
                yield Static("{}", id="lbl-calc-vars", classes="result-box")

                yield Label("[bold]Result / History[/bold]")
                yield RichLog(id="log-calc-eval", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-calc-eval":
            await self.evaluate_expression()
        elif event.button.id == "btn-calc-clear":
            self.query_one("#log-calc-eval", RichLog).clear()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "input-calc-eval":
            await self.evaluate_expression()

    async def evaluate_expression(self) -> None:
        expr = self.query_one("#input-calc-eval", Input).value
        log = self.query_one("#log-calc-eval", RichLog)

        if not expr:
            self.notify("Expression required.", severity="error")
            return

        try:
            result = self.manager.evaluate(expr)
            # Store in special '_' variable
            self.manager.variables['_'] = result

            formatted_result = self.manager.format_result(result)
            # Make sure multiline formatting is printed properly
            output = f"[bold]{expr}[/bold] =\n[green]{formatted_result}[/green]\n"
            log.write(output)

            self.query_one("#input-calc-eval", Input).value = ""

            # Update variables display
            vars_dict = {k: v for k, v in self.manager.variables.items() if k != '_'}
            self.query_one("#lbl-calc-vars", Static).update(str(vars_dict))

        except Exception as e:
            log.write(f"[bold]{expr}[/bold] = [red]Error: {e}[/red]\n")
            self.notify(f"Error: {e}", severity="error")
