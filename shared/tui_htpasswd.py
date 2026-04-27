import pyperclip
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, RichLog, Select
from textual import on

from shared.htpasswd_lab import HtpasswdManager

class HtpasswdLabTab(Container):
    """Tab for HTPasswd Lab - Generate .htpasswd credentials."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = HtpasswdManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]HTPasswd Lab - Generate Credentials[/bold]", classes="welcome-text")

            with Container(classes="stat-box"):
                with Horizontal():
                    with Vertical():
                        yield Label("Username:")
                        yield Input(placeholder="user", id="htpasswd-username")
                    with Vertical():
                        yield Label("Password:")
                        yield Input(placeholder="password", password=True, id="htpasswd-password")

                with Horizontal():
                    with Vertical():
                        yield Label("Algorithm:")
                        yield Select.from_values(["bcrypt", "md5", "sha1", "crypt", "plain"], value="bcrypt", id="htpasswd-algorithm")

                with Horizontal(classes="action-buttons"):
                    yield Button("Generate", id="btn-htpasswd-generate", variant="primary")
                    yield Button("Copy Output", id="btn-htpasswd-copy")

            with VerticalScroll(classes="stat-box", id="htpasswd-output-container"):
                yield Label("[bold]Generated Entry[/bold]")
                yield RichLog(id="htpasswd-output-log", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-htpasswd-generate":
            self.generate_entry()
        elif event.button.id == "btn-htpasswd-copy":
            self.copy_output()

    def generate_entry(self) -> None:
        username = self.query_one("#htpasswd-username", Input).value.strip()
        password = self.query_one("#htpasswd-password", Input).value
        algorithm = str(self.query_one("#htpasswd-algorithm", Select).value)

        output_log = self.query_one("#htpasswd-output-log", RichLog)

        if not username:
            self.notify("Username is required.", severity="error")
            return

        if not password:
            self.notify("Password is required.", severity="error")
            return

        result = self.manager.generate(username, password, algorithm)
        output_log.clear()

        if result["success"]:
            entry = result["entry"]
            output_log.write(entry)
            self._last_generated_entry = entry
            self.notify("Credential generated successfully.")
        else:
            self._last_generated_entry = ""
            error_msg = result.get("error", "Unknown error")
            output_log.write(f"[bold red]Error:[/bold red] {error_msg}")
            self.notify("Failed to generate credential.", severity="error")

    def copy_output(self) -> None:
        entry = getattr(self, "_last_generated_entry", "")
        if entry:
            pyperclip.copy(entry)
            self.notify("Copied to clipboard.")
        else:
            self.notify("No entry generated to copy.", severity="warning")
