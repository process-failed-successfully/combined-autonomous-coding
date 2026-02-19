from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, TabbedContent, TabPane, ProgressBar
from textual.containers import Container, Horizontal, Vertical
from textual.timer import Timer
from shared.otp_lab import OtpLabManager
import time


class OtpLabTab(Container):
    """Tab for OTP operations."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = OtpLabManager()
        self.timer: Timer | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]OTP Lab[/bold]", classes="welcome-text")

            with TabbedContent():
                # Generate Pane
                with TabPane("Generate"):
                    with Vertical(classes="stat-box"):
                        yield Label("Length (default 16):")
                        with Horizontal():
                            yield Input(placeholder="16", id="otp-gen-len", value="16")
                            yield Button("Generate Secret", id="btn-otp-gen", variant="primary")

                        yield Label("[bold]Secret (Base32):[/bold]")
                        yield Input(id="otp-gen-result", disabled=True)

                # Code Pane (TOTP)
                with TabPane("Code"):
                    with Vertical(classes="stat-box"):
                        yield Label("Secret Key:")
                        yield Input(placeholder="Enter Base32 secret...", id="otp-code-secret")

                        yield Label("[bold]Current Code:[/bold]")
                        yield Label("------", id="otp-code-display", classes="code-display")

                        yield Label("Time Remaining:")
                        yield ProgressBar(total=30, id="otp-progress", show_eta=False)

                        yield Button("Start Monitoring", id="btn-otp-monitor", variant="success")
                        yield Button("Stop", id="btn-otp-stop", variant="error", disabled=True)

                # Verify Pane
                with TabPane("Verify"):
                    with Vertical(classes="stat-box"):
                        yield Label("Secret Key:")
                        yield Input(placeholder="Enter Base32 secret...", id="otp-verify-secret")
                        yield Label("Code to Verify:")
                        yield Input(placeholder="123456", id="otp-verify-code")

                        yield Button("Verify", id="btn-otp-verify", variant="primary")
                        yield Label("", id="otp-verify-result")

                # URL Pane
                with TabPane("URL"):
                    with Vertical(classes="stat-box"):
                        yield Label("Secret Key:")
                        yield Input(placeholder="Enter Base32 secret...", id="otp-url-secret")
                        yield Label("Account Label (e.g. user@email.com):")
                        yield Input(placeholder="user@example.com", id="otp-url-label")
                        yield Label("Issuer (Optional):")
                        yield Input(placeholder="MyApp", id="otp-url-issuer")

                        yield Button("Generate URL", id="btn-otp-url", variant="primary")
                        yield Label("[bold]otpauth:// URL:[/bold]")
                        yield Input(id="otp-url-result", disabled=True)

    def on_unmount(self) -> None:
        if self.timer:
            self.timer.stop()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-otp-gen":
            self.generate_secret()
        elif event.button.id == "btn-otp-monitor":
            self.start_monitoring()
        elif event.button.id == "btn-otp-stop":
            self.stop_monitoring()
        elif event.button.id == "btn-otp-verify":
            self.verify_code()
        elif event.button.id == "btn-otp-url":
            self.generate_url()

    def generate_secret(self) -> None:
        length_str = self.query_one("#otp-gen-len", Input).value
        try:
            length = int(length_str) if length_str else 16
            secret = self.manager.generate_secret(length)
            self.query_one("#otp-gen-result", Input).value = secret
            self.notify("Secret generated.")
        except ValueError:
            self.notify("Invalid length.", severity="error")

    def start_monitoring(self) -> None:
        secret = self.query_one("#otp-code-secret", Input).value
        if not secret:
            self.notify("Secret required.", severity="error")
            return

        self.query_one("#btn-otp-monitor").disabled = True
        self.query_one("#btn-otp-stop").disabled = False
        self.query_one("#otp-code-secret").disabled = True

        # Start timer (runs every 0.5s to be smooth)
        self.timer = self.set_interval(0.5, self.update_totp)
        self.update_totp()  # Immediate update

    def stop_monitoring(self) -> None:
        if self.timer:
            self.timer.stop()
            self.timer = None

        self.query_one("#btn-otp-monitor").disabled = False
        self.query_one("#btn-otp-stop").disabled = True
        self.query_one("#otp-code-secret").disabled = False
        self.query_one("#otp-code-display", Label).update("------")
        self.query_one("#otp-progress", ProgressBar).update(total=30, progress=0)

    def update_totp(self) -> None:
        secret = self.query_one("#otp-code-secret", Input).value
        try:
            now = time.time()
            # Calculate remaining time in the 30s window
            remaining = 30 - (now % 30)

            # Update Code
            code = self.manager.generate_totp(secret)
            self.query_one("#otp-code-display", Label).update(f"[bold green size=24]{code}[/]")

            # Update Progress Bar
            self.query_one("#otp-progress", ProgressBar).update(progress=remaining)

        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            self.stop_monitoring()

    def verify_code(self) -> None:
        secret = self.query_one("#otp-verify-secret", Input).value
        code = self.query_one("#otp-verify-code", Input).value
        lbl = self.query_one("#otp-verify-result", Label)

        if not secret or not code:
            self.notify("Secret and Code required.", severity="error")
            return

        try:
            valid = self.manager.verify_totp(secret, code)
            if valid:
                lbl.update("[bold green]✅ VALID[/bold green]")
            else:
                lbl.update("[bold red]❌ INVALID[/bold red]")
        except Exception as e:
            lbl.update(f"[red]Error: {e}[/red]")

    def generate_url(self) -> None:
        secret = self.query_one("#otp-url-secret", Input).value
        label = self.query_one("#otp-url-label", Input).value
        issuer = self.query_one("#otp-url-issuer", Input).value

        if not secret or not label:
            self.notify("Secret and Label required.", severity="error")
            return

        try:
            url = self.manager.generate_url(secret, label, issuer)
            self.query_one("#otp-url-result", Input).value = url
            self.notify("URL generated.")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
