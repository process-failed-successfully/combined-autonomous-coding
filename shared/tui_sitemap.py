from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import TabPane, Label, Input, Button, TextArea, Static, DataTable

from shared.sitemap_lab import SitemapManager

class SitemapLabTab(TabPane):
    """Sitemap Lab TUI for parsing and exploring XML sitemaps."""

    def __init__(self):
        super().__init__("Sitemap Lab", id="tab-sitemap")
        self.manager = SitemapManager()

    def compose(self) -> ComposeResult:
        with Vertical(id="sitemap-layout"):
            yield Label("Sitemap Content or URL", classes="section-header")

            with Horizontal(id="sitemap-fetch-bar", classes="mb-1"):
                yield Input(placeholder="Enter URL to fetch (e.g., https://example.com/sitemap.xml)", id="sitemap-url-input")
                yield Button("Fetch", id="sitemap-fetch-btn", variant="primary")

            yield TextArea(id="sitemap-content-area", classes="mb-1")

            with Horizontal(id="sitemap-parse-bar", classes="mb-1"):
                yield Button("Parse", id="sitemap-parse-btn", variant="success")
                yield Static("", id="sitemap-parse-status", classes="ml-1")

            yield Label("Sitemap URLs", classes="section-header")
            yield DataTable(id="sitemap-data-table", classes="mb-1")

    def on_mount(self) -> None:
        table = self.query_one("#sitemap-data-table", DataTable)
        table.add_columns("URL", "Last Modified", "Change Frequency", "Priority")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sitemap-fetch-btn":
            url_input = self.query_one("#sitemap-url-input", Input)
            url = url_input.value.strip()

            if not url:
                self._update_status("Error: Please provide a URL to fetch.", error=True)
                return

            self._update_status("Fetching...")

            content = self.manager.fetch(url)
            text_area = self.query_one("#sitemap-content-area", TextArea)
            text_area.text = content

            if "Error fetching" in content or "Unexpected error" in content:
                self._update_status("Fetch failed.", error=True)
            else:
                self._update_status("Fetch successful.", error=False)

        elif event.button.id == "sitemap-parse-btn":
            text_area = self.query_one("#sitemap-content-area", TextArea)
            content = text_area.text.strip()

            if not content:
                self._update_status("Error: No sitemap content provided.", error=True)
                return

            table = self.query_one("#sitemap-data-table", DataTable)
            table.clear()

            try:
                parsed = self.manager.parse(content)
                if parsed["type"] == "error":
                    self._update_status("Error parsing sitemap.", error=True)
                    return
                elif parsed["type"] == "unknown":
                    self._update_status("Unknown sitemap format.", error=True)
                    return

                for url_data in parsed["urls"]:
                    table.add_row(
                        url_data.get("loc", ""),
                        url_data.get("lastmod", ""),
                        url_data.get("changefreq", ""),
                        url_data.get("priority", "")
                    )

                self._update_status(f"Parsed {parsed['type']} with {len(parsed['urls'])} URLs.", error=False)

            except Exception as e:
                self._update_status(f"Error parsing: {e}", error=True)

    def _update_status(self, message: str, error: bool = False):
        status_label = self.query_one("#sitemap-parse-status", Static)
        if error:
            status_label.update(f"[red]{message}[/red]")
        else:
            status_label.update(f"[green]{message}[/green]")
