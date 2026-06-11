from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import TabPane, Label, Input, Button, TextArea, Static

from shared.robots_txt_lab import RobotsTxtManager

class RobotsTxtLabTab(TabPane):
    """Robots.txt Lab TUI for parsing and verifying robots.txt files."""

    def __init__(self):
        super().__init__("Robots.txt Lab", id="tab-robots")
        self.manager = RobotsTxtManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="robots-txt-layout"):
            yield Label("Robots.txt Content or URL", classes="section-header")

            with Horizontal(id="robots-fetch-bar", classes="mb-1"):
                yield Input(placeholder="Enter URL to fetch (e.g., https://example.com/robots.txt)", id="robots-url-input")
                yield Button("Fetch", id="robots-fetch-btn", variant="primary")

            yield TextArea(id="robots-content-area", classes="mb-1")

            yield Label("Check Permissions", classes="section-header")

            with Horizontal(id="robots-check-bar", classes="mb-1"):
                yield Input(placeholder="User Agent (e.g., Googlebot)", id="robots-ua-input")
                yield Input(placeholder="Path (e.g., /admin/)", id="robots-path-input")
                yield Button("Check", id="robots-check-btn", variant="success")

            yield Static(id="robots-result-output", classes="output-panel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "robots-fetch-btn":
            url_input = self.query_one("#robots-url-input", Input)
            url = url_input.value.strip()

            if not url:
                self._update_result("Error: Please provide a URL to fetch.", error=True)
                return

            self._update_result("Fetching...")

            content = self.manager.fetch(url)
            text_area = self.query_one("#robots-content-area", TextArea)
            text_area.text = content

            if "Error fetching" in content or "Unexpected error" in content:
                self._update_result("Fetch failed.", error=True)
            else:
                self._update_result("Fetch successful.", error=False)

        elif event.button.id == "robots-check-btn":
            text_area = self.query_one("#robots-content-area", TextArea)
            content = text_area.text.strip()

            if not content:
                self._update_result("Error: No robots.txt content provided.", error=True)
                return

            ua_input = self.query_one("#robots-ua-input", Input)
            user_agent = ua_input.value.strip() or "*"

            path_input = self.query_one("#robots-path-input", Input)
            path = path_input.value.strip() or "/"

            try:
                self.manager.parse(content)
                allowed = self.manager.check(user_agent, path)

                if allowed:
                    msg = f"✅ ALLOWED: '{user_agent}' can fetch '{path}'"
                    self._update_result(msg, error=False)
                else:
                    msg = f"❌ DISALLOWED: '{user_agent}' cannot fetch '{path}'"
                    self._update_result(msg, error=True)
            except Exception as e:
                self._update_result(f"Error parsing or checking: {e}", error=True)

    def _update_result(self, message: str, error: bool = False):
        output = self.query_one("#robots-result-output", Static)
        if error:
            output.update(f"[red]{message}[/red]")
        else:
            output.update(f"[green]{message}[/green]")
