import json
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.widgets import Label, Input, Button, Checkbox, TextArea, Select
from textual import on
from shared.cookie_lab import CookieLabManager


class CookieLabTab(VerticalScroll):
    """TUI tab for managing HTTP Cookies."""

    def __init__(self, project_dir: Path | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CookieLabManager()

    def compose(self) -> ComposeResult:
        yield Label("[bold]Cookie Lab[/bold]", classes="welcome-text")

        # Parser Section
        with Vertical(classes="stat-box"):
            yield Label("[bold]Parse Cookie[/bold]")
            yield Label("Enter a raw Cookie or Set-Cookie header string:")
            yield Input(placeholder="session_id=123; Path=/; Secure; HttpOnly", id="cookie-parse-input")
            yield Button("Parse", id="btn-cookie-parse", variant="primary")
            yield TextArea(id="cookie-parse-output", read_only=True, language="json")

        # Generator Section
        with Vertical(classes="stat-box"):
            yield Label("[bold]Generate Set-Cookie[/bold]")
            with Horizontal():
                yield Input(placeholder="Key (e.g. session_id)", id="cookie-gen-key")
                yield Input(placeholder="Value (e.g. 12345)", id="cookie-gen-value")

            with Horizontal():
                yield Input(placeholder="Domain (optional)", id="cookie-gen-domain")
                yield Input(placeholder="Path (default: /)", id="cookie-gen-path", value="/")
                yield Input(placeholder="Expires (optional)", id="cookie-gen-expires")

            with Horizontal():
                yield Input(placeholder="Max-Age (seconds, optional)", id="cookie-gen-max-age", type="integer")
                yield Select.from_values(["Strict", "Lax", "None", ""], prompt="SameSite", id="cookie-gen-samesite")

            with Horizontal():
                yield Checkbox("Secure", id="cookie-gen-secure", value=False)
                yield Checkbox("HttpOnly", id="cookie-gen-httponly", value=False)

            yield Button("Generate", id="btn-cookie-generate", variant="warning")
            yield Input(placeholder="Generated Set-Cookie string will appear here...", id="cookie-gen-output", read_only=True)

    @on(Button.Pressed, "#btn-cookie-parse")
    def on_parse(self, event: Button.Pressed) -> None:
        cookie_string = self.query_one("#cookie-parse-input", Input).value
        if not cookie_string:
            self.notify("Please enter a cookie string to parse.", severity="warning")
            return

        res = self.manager.parse_cookie(cookie_string)
        output = self.query_one("#cookie-parse-output", TextArea)

        if "error" in res:
            output.text = f"Error: {res['error']}"
        else:
            output.text = json.dumps(res, indent=2)

    @on(Button.Pressed, "#btn-cookie-generate")
    def on_generate(self, event: Button.Pressed) -> None:
        key = self.query_one("#cookie-gen-key", Input).value
        value = self.query_one("#cookie-gen-value", Input).value

        if not key or not value:
            self.notify("Key and Value are required.", severity="error")
            return

        kwargs = {}
        domain = self.query_one("#cookie-gen-domain", Input).value
        path = self.query_one("#cookie-gen-path", Input).value
        expires = self.query_one("#cookie-gen-expires", Input).value
        max_age = self.query_one("#cookie-gen-max-age", Input).value
        samesite = self.query_one("#cookie-gen-samesite", Select).value
        secure = self.query_one("#cookie-gen-secure", Checkbox).value
        httponly = self.query_one("#cookie-gen-httponly", Checkbox).value

        if domain:
            kwargs["domain"] = domain
        if path:
            kwargs["path"] = path
        if expires:
            kwargs["expires"] = expires
        if max_age:
            kwargs["max-age"] = max_age
        if samesite and samesite != Select.BLANK:
            kwargs["samesite"] = samesite
        if secure:
            kwargs["secure"] = True
        if httponly:
            kwargs["httponly"] = True

        try:
            res = self.manager.generate_cookie(key, value, **kwargs)
            self.query_one("#cookie-gen-output", Input).value = res["set_cookie"]
        except Exception as e:
            self.notify(f"Generation error: {str(e)}", severity="error")
