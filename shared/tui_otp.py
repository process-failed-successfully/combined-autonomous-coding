from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, ProgressBar, TabbedContent, TabPane, Static
from textual import on
import time
from shared.otp_lab import OtpLabManager

class OtpLabTab(Container):
    """Tab for OTP operations (Generate Secret, Code, Verify)."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = OtpLabManager()
        self.current_secret = ""
        self.timer = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]OTP Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Generator Pane
                with TabPane("Generator"):
                    with Vertical(classes="stat-box"):
                        yield Label("Label (e.g. user@example.com):")
                        yield Input(placeholder="user@example.com", id="otp-gen-label")
                        yield Label("Issuer (e.g. MyApp):")
                        yield Input(placeholder="MyApp", id="otp-gen-issuer")
                        yield Button("Generate New Secret", id="btn-otp-generate", variant="primary")

                    with Vertical(classes="stat-box"):
                        yield Label("Secret (Base32):")
                        yield Input(id="otp-gen-secret", read_only=True)

                        yield Label("Current Code:", classes="label")
                        yield Label("------", id="otp-code-display", classes="welcome-text") # Big text

                        yield Label("Time Remaining:")
                        yield ProgressBar(total=30, show_eta=False, id="otp-progress")

                        yield Label("OTP Auth URL:")
                        yield Input(id="otp-url-display", read_only=True)

                # Verify Pane
                with TabPane("Verify"):
                    with Vertical(classes="stat-box"):
                        yield Label("Secret:")
                        yield Input(placeholder="Base32 Secret...", id="otp-verify-secret")
                        yield Label("Code:")
                        yield Input(placeholder="123456", id="otp-verify-code")
                        yield Button("Verify", id="btn-otp-verify", variant="success")

                    yield Label("[bold]Result[/bold]")
                    yield Label("", id="otp-verify-result")

    def on_mount(self) -> None:
        # Update every 0.1s for smooth progress bar
        self.timer = self.set_interval(0.1, self.update_timer)
        # Generate initial secret if empty
        if not self.current_secret:
            self.generate_new_secret()

    def update_timer(self) -> None:
        if not self.current_secret:
            return

        now = time.time()
        interval = 30
        remaining = interval - (now % interval)

        # Update Progress Bar
        bar = self.query_one("#otp-progress", ProgressBar)
        bar.update(total=interval, progress=remaining)

        # Update Code
        # We only need to update code when remaining is close to 30 (new interval)
        # But easier to just update periodically or check if changed.
        # Let's generate and compare.
        try:
            code = self.manager.generate_totp(self.current_secret)
            display = self.query_one("#otp-code-display", Label)
            if display.renderable != code:
                display.update(code)
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-otp-generate":
            self.generate_new_secret()
        elif event.button.id == "btn-otp-verify":
            self.verify_code()

    def generate_new_secret(self) -> None:
        try:
            self.current_secret = self.manager.generate_secret()

            # Update UI
            self.query_one("#otp-gen-secret", Input).value = self.current_secret

            label = self.query_one("#otp-gen-label", Input).value or "user@example.com"
            issuer = self.query_one("#otp-gen-issuer", Input).value or "MyApp"

            url = self.manager.generate_url(self.current_secret, label, issuer)
            self.query_one("#otp-url-display", Input).value = url

            # Force update code immediately
            self.update_timer()

            self.notify("New secret generated.")
        except Exception as e:
            self.notify(f"Error generating secret: {e}", severity="error")

    def verify_code(self) -> None:
        secret = self.query_one("#otp-verify-secret", Input).value
        code = self.query_one("#otp-verify-code", Input).value
        result_lbl = self.query_one("#otp-verify-result", Label)

        if not secret or not code:
            self.notify("Secret and Code required.", severity="error")
            return

        try:
            valid = self.manager.verify_totp(secret, code)
            if valid:
                result_lbl.update("[bold green]✅ VALID[/bold green]")
                self.notify("Code is valid.")
            else:
                result_lbl.update("[bold red]❌ INVALID[/bold red]")
                self.notify("Code is invalid.", severity="error")
        except Exception as e:
            result_lbl.update(f"[bold red]Error: {e}[/bold red]")
            self.notify(f"Verification error: {e}", severity="error")
