from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, TextArea, Select, Button, RichLog
from textual import on
from shared.token_lab import TokenLabManager


class TokenLabTab(Container):
    """Tab for counting and viewing tokens."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = TokenLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Token Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Label("Model:")
                yield Select.from_values(
                    ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "text-davinci-003", "text-embedding-ada-002"],
                    id="token-model-select", value="gpt-4o"
                )
                yield Label("Encoding:")
                yield Select.from_values(
                    ["cl100k_base", "p50k_base", "r50k_base", "o200k_base"],
                    id="token-encoding-select", value="cl100k_base"
                )
                yield Button("Count Tokens", id="btn-token-count", variant="primary")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("Text Input:")
                    yield TextArea(id="token-text-input")

                with Vertical(classes="stat-box"):
                    yield Label("Results:")
                    yield RichLog(id="token-result-log", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-token-count")
    def count_tokens(self) -> None:
        text = self.query_one("#token-text-input", TextArea).text
        if not text:
            self.notify("Please enter some text.", severity="warning")
            return

        model = self.query_one("#token-model-select", Select).value or "gpt-4o"
        encoding = self.query_one("#token-encoding-select", Select).value

        log = self.query_one("#token-result-log", RichLog)
        log.clear()

        try:
            count_model = self.manager.count_tokens(text, model)
            count_enc = self.manager.count_tokens_by_encoding(text, encoding)
            tokens = self.manager.get_tokens(text, model)

            log.write(f"[bold green]Token Count ({model}):[/bold green] {count_model}")
            log.write(f"[bold cyan]Token Count ({encoding}):[/bold cyan] {count_enc}")
            log.write(f"[bold]Character Count:[/bold] {len(text)}")
            log.write("")
            log.write(f"[bold]Token IDs ({model}):[/bold]")

            # Show a sample of the tokens
            token_str = ", ".join(str(t) for t in tokens[:50])
            if len(tokens) > 50:
                token_str += ", ..."
            log.write(token_str)

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Error counting tokens: {e}", severity="error")
