import sys
import io
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Input, Button, RichLog
from textual import on
from shared.seo_lab import SeoLabManager

class SeoLabTab(Container):
    """Tab for SEO Lab operations."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]SEO Lab[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("Analyze URL:")
                with Horizontal():
                    yield Input(placeholder="https://example.com", id="seo-url-input")
                    yield Button("Analyze URL", id="btn-seo-url", variant="primary")

                yield Label("Analyze Local File:")
                with Horizontal():
                    yield Input(placeholder="path/to/file.html", id="seo-file-input")
                    yield Button("Analyze File", id="btn-seo-file", variant="primary")

            yield Label("Report:")
            yield RichLog(id="seo-report-log", wrap=True, highlight=False, markup=False)

    @on(Button.Pressed, "#btn-seo-url")
    def on_analyze_url(self) -> None:
        url = self.query_one("#seo-url-input", Input).value
        log = self.query_one("#seo-report-log", RichLog)
        log.clear()

        if not url:
            log.write("Error: Please provide a URL.")
            return

        manager = SeoLabManager()
        log.write(f"Analyzing URL: {url}...\n")
        try:
            stats = manager.analyze_url(url)
            self._write_report_to_log(manager, stats, log)
        except Exception as e:
            log.write(f"Error analyzing URL: {e}")

    @on(Button.Pressed, "#btn-seo-file")
    def on_analyze_file(self) -> None:
        filepath = self.query_one("#seo-file-input", Input).value
        log = self.query_one("#seo-report-log", RichLog)
        log.clear()

        if not filepath:
            log.write("Error: Please provide a file path.")
            return

        manager = SeoLabManager()
        log.write(f"Analyzing File: {filepath}...\n")
        try:
            stats = manager.analyze_file(filepath)
            self._write_report_to_log(manager, stats, log)
        except Exception as e:
            log.write(f"Error analyzing file: {e}")

    def _write_report_to_log(self, manager, stats, log):
        # Capture the stdout of generate_report to display it in the RichLog
        old_stdout = sys.stdout
        sys.stdout = capture = io.StringIO()
        try:
            manager.generate_report(stats, output_format="text")
        finally:
            sys.stdout = old_stdout

        log.write(capture.getvalue())
