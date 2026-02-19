from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, DataTable, RichLog, TabbedContent, TabPane, Static
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
import asyncio
from shared.math_lab import MathLabManager

class MathLabTab(Container):
    """Tab for Math operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = MathLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Math Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Evaluate Pane
                with TabPane("Evaluate"):
                    with Vertical(classes="stat-box"):
                        yield Label("Expression:")
                        with Horizontal():
                            yield Input(placeholder="e.g. 2 + 2 * 4, pow(2, 10), sqrt(16)...", id="input-math-eval")
                            yield Button("Calculate", id="btn-math-eval", variant="primary")

                        yield Label("[bold]Result / History[/bold]")
                        yield RichLog(id="log-math-eval", wrap=True, highlight=True, markup=True)

                # Statistics Pane
                with TabPane("Statistics"):
                    with Vertical(classes="stat-box"):
                        yield Label("Numbers (comma or space separated):")
                        with Horizontal():
                            yield Input(placeholder="e.g. 1, 2, 3, 4, 5", id="input-math-stats")
                            yield Button("Analyze", id="btn-math-stats", variant="primary")

                        yield Label("[bold]Results[/bold]")
                        yield DataTable(id="table-math-stats")

                # Primes Pane
                with TabPane("Primes"):
                    with Vertical(classes="stat-box"):
                        yield Label("Integer:")
                        with Horizontal():
                            yield Input(placeholder="e.g. 13", id="input-math-prime")
                            yield Button("Check Prime", id="btn-math-check-prime", variant="primary")
                            yield Button("Next Prime", id="btn-math-next-prime", variant="warning")
                            yield Button("Factors", id="btn-math-factors", variant="success")

                        yield Label("[bold]Result[/bold]")
                        yield Static(id="lbl-math-prime-result", classes="result-box")

    def on_mount(self) -> None:
        # Init Stats Table
        table = self.query_one("#table-math-stats", DataTable)
        table.cursor_type = "row"
        table.add_columns("Metric", "Value")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-math-eval":
            await self.evaluate_expression()
        elif event.button.id == "btn-math-stats":
            await self.calculate_statistics()
        elif event.button.id == "btn-math-check-prime":
            await self.check_prime()
        elif event.button.id == "btn-math-next-prime":
            await self.find_next_prime()
        elif event.button.id == "btn-math-factors":
            await self.find_prime_factors()

    async def evaluate_expression(self) -> None:
        expr = self.query_one("#input-math-eval", Input).value
        log = self.query_one("#log-math-eval", RichLog)

        if not expr:
            self.notify("Expression required.", severity="error")
            return

        try:
            # Evaluate is usually fast enough to be sync, but good practice to be consistent
            result = self.manager.evaluate(expr)
            log.write(f"[bold]{expr}[/bold] = [green]{result}[/green]")
            self.query_one("#input-math-eval", Input).value = ""
        except Exception as e:
            log.write(f"[bold]{expr}[/bold] = [red]Error: {e}[/red]")
            self.notify(f"Error: {e}", severity="error")

    async def calculate_statistics(self) -> None:
        raw_input = self.query_one("#input-math-stats", Input).value
        table = self.query_one("#table-math-stats", DataTable)

        if not raw_input:
            self.notify("Numbers required.", severity="error")
            return

        numbers = []
        try:
            # Handle comma and space separation
            parts = raw_input.replace(",", " ").split()
            numbers = [float(p) for p in parts]
        except ValueError:
            self.notify("Invalid number format.", severity="error")
            return

        if not numbers:
            self.notify("No valid numbers found.", severity="error")
            return

        # Calculate stats
        try:
            stats = self.manager.calculate_stats(numbers)
            table.clear()
            for k, v in stats.items():
                val_display = "N/A" if v is None else f"{v:.4f}"
                if isinstance(v, int):
                    val_display = str(v)
                table.add_row(k.capitalize(), val_display)
            self.notify("Statistics calculated.")
        except Exception as e:
            self.notify(f"Error calculating stats: {e}", severity="error")

    async def check_prime(self) -> None:
        val_str = self.query_one("#input-math-prime", Input).value
        lbl = self.query_one("#lbl-math-prime-result", Static)

        try:
            n = int(val_str)
        except ValueError:
            self.notify("Integer required.", severity="error")
            return

        lbl.update("Checking...")

        try:
            is_prime = await asyncio.to_thread(self.manager.is_prime, n)
            if is_prime:
                lbl.update(f"[green]✅ {n} is prime.[/green]")
            else:
                lbl.update(f"[red]❌ {n} is NOT prime.[/red]")
        except Exception as e:
            lbl.update(f"[red]Error: {e}[/red]")

    async def find_next_prime(self) -> None:
        val_str = self.query_one("#input-math-prime", Input).value
        lbl = self.query_one("#lbl-math-prime-result", Static)

        try:
            n = int(val_str)
        except ValueError:
            self.notify("Integer required.", severity="error")
            return

        lbl.update("Calculating...")

        try:
            next_p = await asyncio.to_thread(self.manager.next_prime, n)
            lbl.update(f"Next prime after {n} is [bold green]{next_p}[/bold green]")
        except Exception as e:
            lbl.update(f"[red]Error: {e}[/red]")

    async def find_prime_factors(self) -> None:
        val_str = self.query_one("#input-math-prime", Input).value
        lbl = self.query_one("#lbl-math-prime-result", Static)

        try:
            n = int(val_str)
        except ValueError:
            self.notify("Integer required.", severity="error")
            return

        lbl.update("Factoring...")

        try:
            factors = await asyncio.to_thread(self.manager.prime_factors, n)
            lbl.update(f"Prime factors of {n}: [bold cyan]{factors}[/bold cyan]")
        except Exception as e:
            lbl.update(f"[red]Error: {e}[/red]")
