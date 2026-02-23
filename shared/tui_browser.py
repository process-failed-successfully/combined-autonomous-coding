from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, RichLog, TabbedContent, TabPane, TextArea
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on
from rich.syntax import Syntax

from shared.browser_lab import BrowserLabManager

class BrowserLabTab(Container):
    """Tab for Web Browsing and Inspection."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = BrowserLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Browser Lab[/bold]", classes="welcome-text")

            # Address Bar
            with Horizontal(classes="stat-box"):
                yield Input(placeholder="https://example.com", id="browser-url")
                yield Button("Go", id="btn-browser-go", variant="primary")
                yield Button("Screenshot", id="btn-browser-shot", variant="success")
                yield Button("Inspect", id="btn-browser-inspect", variant="warning")

            with TabbedContent():
                with TabPane("Preview"):
                    with VerticalScroll(id="browser-preview-container"):
                        yield RichLog(id="browser-preview-log", wrap=True, highlight=True, markup=True)

                with TabPane("HTML"):
                    yield TextArea(id="browser-html-editor", language="html", read_only=True)

                with TabPane("Metadata"):
                    yield RichLog(id="browser-meta-log", wrap=True, highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-browser-go":
            await self.navigate()
        elif event.button.id == "btn-browser-shot":
            await self.screenshot()
        elif event.button.id == "btn-browser-inspect":
            await self.inspect()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "browser-url":
            await self.navigate()

    async def navigate(self) -> None:
        url = self.query_one("#browser-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        preview_log = self.query_one("#browser-preview-log", RichLog)
        html_editor = self.query_one("#browser-html-editor", TextArea)

        preview_log.clear()
        preview_log.write(f"Loading {url}...")
        self.notify(f"Loading {url}...")

        import asyncio
        try:
            # Fetch Text
            text = await self.manager.get_text(url)
            preview_log.clear()
            preview_log.write(text)

            # Fetch HTML (separate call, maybe optimized in future)
            html = await self.manager.get_html(url)
            html_editor.text = html

            self.notify("Page loaded.")

        except ImportError as e:
            preview_log.write(f"[bold red]Dependency Error:[/bold red] {e}")
            self.notify("Playwright missing.", severity="error")
        except Exception as e:
            preview_log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Error: {e}", severity="error")

    async def screenshot(self) -> None:
        url = self.query_one("#browser-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        self.notify("Taking screenshot...")

        output_path = self.project_dir / "screenshot.png"

        import asyncio
        try:
            path = await self.manager.screenshot(url, output_path)
            self.notify(f"Screenshot saved to {path}")
            # Could potentially display it using ImageLab if integrated,
            # but for now just notify.
        except Exception as e:
            self.notify(f"Screenshot failed: {e}", severity="error")

    async def inspect(self) -> None:
        url = self.query_one("#browser-url", Input).value
        if not url:
            self.notify("URL required.", severity="error")
            return

        meta_log = self.query_one("#browser-meta-log", RichLog)
        meta_log.clear()
        meta_log.write(f"Inspecting {url}...")

        import asyncio
        try:
            info = await self.manager.inspect(url)

            meta_log.write(f"[bold]Title:[/bold] {info['title']}")
            meta_log.write(f"[bold]URL:[/bold] {info['url']}")

            if info['meta']:
                meta_log.write("\n[bold]Meta Tags:[/bold]")
                for m in info['meta']:
                    for k, v in m.items():
                        meta_log.write(f"  {k}: {v}")
            else:
                meta_log.write("\nNo meta tags found.")

            self.notify("Inspection complete.")

        except Exception as e:
            meta_log.write(f"[bold red]Error:[/bold red] {e}")
