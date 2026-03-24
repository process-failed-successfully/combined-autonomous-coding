from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, TextArea, Select, Input, Static
from textual import on

from shared.bcrypt_lab import BcryptLabManager

class BcryptLabTab(Container):
    """Tab for Bcrypt hashing and verification."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = BcryptLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Bcrypt Lab[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("Generate Hash")
                    yield Label("Password:")
                    yield Input(placeholder="Enter password...", id="bcrypt-gen-password", password=True)
                    yield Label("Cost Factor (Rounds):")
                    rounds_options = [(str(i), i) for i in range(4, 32)]
                    yield Select(options=rounds_options, id="bcrypt-rounds", value=12)
                    yield Button("Generate", id="btn-bcrypt-generate", variant="primary")
                    yield Label("Result Hash:")
                    yield TextArea(id="bcrypt-gen-result", read_only=True)

                with Vertical(classes="stat-box"):
                    yield Label("Verify Hash")
                    yield Label("Password:")
                    yield Input(placeholder="Enter password to verify...", id="bcrypt-ver-password", password=True)
                    yield Label("Hash String:")
                    yield Input(placeholder="$2b$12$...", id="bcrypt-ver-hash")
                    yield Button("Verify", id="btn-bcrypt-verify", variant="warning")
                    yield Label("Result:")
                    yield Static("", id="bcrypt-ver-result")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-bcrypt-generate":
            self.action_generate()
        elif event.button.id == "btn-bcrypt-verify":
            self.action_verify()

    def action_generate(self) -> None:
        password = self.query_one("#bcrypt-gen-password", Input).value
        if not password:
            self.notify("Password required for generation.", severity="error")
            return

        rounds = self.query_one("#bcrypt-rounds", Select).value
        if rounds is None:
            rounds = 12

        try:
            hashed = self.manager.hash_password(password, rounds=rounds)
            self.query_one("#bcrypt-gen-result", TextArea).text = hashed
            self.notify("Hash generated successfully.")
        except Exception as e:
            self.notify(f"Generation error: {e}", severity="error")

    def action_verify(self) -> None:
        password = self.query_one("#bcrypt-ver-password", Input).value
        hashed = self.query_one("#bcrypt-ver-hash", Input).value

        if not password or not hashed:
            self.notify("Both password and hash string are required for verification.", severity="error")
            return

        result_static = self.query_one("#bcrypt-ver-result", Static)

        try:
            is_valid = self.manager.verify_password(password, hashed)
            if is_valid:
                result_static.update("[bold green]Match: True[/bold green]")
                self.notify("Password verified: Match.")
            else:
                result_static.update("[bold red]Match: False[/bold red]")
                self.notify("Password verified: No match.", severity="warning")
        except Exception as e:
            result_static.update(f"[bold red]Error: {e}[/bold red]")
            self.notify(f"Verification error: {e}", severity="error")
