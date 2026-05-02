from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, TextArea, Select, Input, Static
from textual import on

from shared.argon2_lab import Argon2LabManager

class Argon2LabTab(Container):
    """Tab for Argon2 hashing and verification."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Argon2LabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Argon2 Lab[/bold]", classes="welcome-text")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("Generate Hash")
                    yield Label("Password:")
                    yield Input(placeholder="Enter password...", id="argon2-gen-password", password=True)
                    yield Label("Time Cost (Iterations):")
                    yield Input(value="3", id="argon2-time", type="integer")
                    yield Label("Memory Cost (KiB):")
                    yield Input(value="65536", id="argon2-memory", type="integer")
                    yield Label("Parallelism (Threads):")
                    yield Input(value="4", id="argon2-parallelism", type="integer")
                    yield Label("Hash Length:")
                    yield Input(value="32", id="argon2-hash-len", type="integer")
                    yield Button("Generate", id="btn-argon2-generate", variant="primary")
                    yield Label("Result Hash:")
                    yield TextArea(id="argon2-gen-result", read_only=True)

                with Vertical(classes="stat-box"):
                    yield Label("Verify Hash")
                    yield Label("Password:")
                    yield Input(placeholder="Enter password to verify...", id="argon2-ver-password", password=True)
                    yield Label("Hash String:")
                    yield Input(placeholder="$argon2id$...", id="argon2-ver-hash")
                    yield Button("Verify", id="btn-argon2-verify", variant="warning")
                    yield Label("Result:")
                    yield Static("", id="argon2-ver-result")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-argon2-generate":
            self.action_generate()
        elif event.button.id == "btn-argon2-verify":
            self.action_verify()

    def action_generate(self) -> None:
        password = self.query_one("#argon2-gen-password", Input).value
        if not password:
            self.notify("Password required for generation.", severity="error")
            return

        try:
            time_cost = int(self.query_one("#argon2-time", Input).value)
            memory_cost = int(self.query_one("#argon2-memory", Input).value)
            parallelism = int(self.query_one("#argon2-parallelism", Input).value)
            hash_len = int(self.query_one("#argon2-hash-len", Input).value)
        except ValueError:
            self.notify("Cost parameters must be valid integers.", severity="error")
            return

        try:
            hashed = self.manager.hash_password(
                password=password,
                time_cost=time_cost,
                memory_cost=memory_cost,
                parallelism=parallelism,
                hash_len=hash_len
            )
            self.query_one("#argon2-gen-result", TextArea).text = hashed
            self.notify("Hash generated successfully.")
        except Exception as e:
            self.notify(f"Generation error: {e}", severity="error")

    def action_verify(self) -> None:
        password = self.query_one("#argon2-ver-password", Input).value
        hashed = self.query_one("#argon2-ver-hash", Input).value

        if not password or not hashed:
            self.notify("Both password and hash string are required for verification.", severity="error")
            return

        result_static = self.query_one("#argon2-ver-result", Static)

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
