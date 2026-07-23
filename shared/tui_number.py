from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, Button, Input, Select, TabbedContent, TabPane, RichLog
from textual import on
from shared.number_lab import NumberLabManager


class NumberLabTab(Container):
    """Tab for Number Lab operations."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Number Lab[/bold]", classes="welcome-text")

            with TabbedContent(id="num-tabs"):
                with TabPane("Conversion", id="num-tab-convert"):
                    with Vertical(classes="stat-box"):
                        yield Label("Number:")
                        yield Input(placeholder="e.g. 255, 0xFF, 0b1010", id="num-convert-input")
                        yield Label("Convert To Base:")
                        yield Select.from_values(
                            [("Binary (2)", 2), ("Octal (8)", 8), ("Decimal (10)", 10), ("Hexadecimal (16)", 16)],
                            id="num-convert-base", value=16
                        )
                        yield Button("Convert", id="btn-num-convert", variant="primary")
                        yield RichLog(id="num-convert-result", wrap=True, highlight=False, markup=True)

                with TabPane("Prime Checker", id="num-tab-prime"):
                    with Vertical(classes="stat-box"):
                        yield Label("Number:")
                        yield Input(placeholder="e.g. 17", id="num-prime-input")
                        yield Button("Check Prime", id="btn-num-prime", variant="primary")
                        yield RichLog(id="num-prime-result", wrap=True, highlight=False, markup=True)

                with TabPane("Factors", id="num-tab-factors"):
                    with Vertical(classes="stat-box"):
                        yield Label("Number:")
                        yield Input(placeholder="e.g. 100", id="num-factors-input")
                        yield Button("Get Prime Factors", id="btn-num-factors", variant="primary")
                        yield RichLog(id="num-factors-result", wrap=True, highlight=False, markup=True)

                with TabPane("Statistics", id="num-tab-stats"):
                    with Vertical(classes="stat-box"):
                        yield Label("Numbers (space separated):")
                        yield Input(placeholder="e.g. 1 2 3 4 5", id="num-stats-input")
                        yield Button("Calculate Stats", id="btn-num-stats", variant="primary")
                        yield RichLog(id="num-stats-result", wrap=True, highlight=False, markup=True)

    @on(Button.Pressed, "#btn-num-convert")
    def on_convert(self) -> None:
        num_str = self.query_one("#num-convert-input", Input).value
        to_base = self.query_one("#num-convert-base", Select).value
        log = self.query_one("#num-convert-result", RichLog)
        log.clear()

        if not num_str:
            log.write("[bold red]Please enter a number.[/bold red]")
            return

        manager = NumberLabManager()
        try:
            result = manager.convert(num_str, int(to_base))
            log.write(f"[bold green]Result:[/bold green] {result}")
        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-num-prime")
    def on_prime(self) -> None:
        num_str = self.query_one("#num-prime-input", Input).value
        log = self.query_one("#num-prime-result", RichLog)
        log.clear()

        if not num_str:
            log.write("[bold red]Please enter a number.[/bold red]")
            return

        manager = NumberLabManager()
        try:
            is_prime = manager.is_prime(num_str)
            if is_prime:
                log.write(f"[bold green]{num_str} is a PRIME number.[/bold green]")
            else:
                log.write(f"[bold yellow]{num_str} is NOT a prime number.[/bold yellow]")
        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-num-factors")
    def on_factors(self) -> None:
        num_str = self.query_one("#num-factors-input", Input).value
        log = self.query_one("#num-factors-result", RichLog)
        log.clear()

        if not num_str:
            log.write("[bold red]Please enter a number.[/bold red]")
            return

        manager = NumberLabManager()
        try:
            factors = manager.factors(num_str)
            log.write(f"[bold green]Prime factors:[/bold green] {', '.join(map(str, factors))}")
        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")

    @on(Button.Pressed, "#btn-num-stats")
    def on_stats(self) -> None:
        num_str = self.query_one("#num-stats-input", Input).value
        log = self.query_one("#num-stats-result", RichLog)
        log.clear()

        if not num_str:
            log.write("[bold red]Please enter numbers.[/bold red]")
            return

        manager = NumberLabManager()
        try:
            stats = manager.stats(num_str.split())
            log.write("[bold cyan]--- Statistics ---[/bold cyan]")
            for k, v in stats.items():
                log.write(f"[bold]{k.capitalize()}:[/bold] {v}")
        except ValueError as e:
            log.write(f"[bold red]Error: {e}[/bold red]")
