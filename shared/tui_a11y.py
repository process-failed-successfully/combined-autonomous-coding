from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Button, DataTable, Input, Static, Label
from textual import on
from pathlib import Path

from shared.a11y import AccessibilityScanner


class A11yTab(Container):
    """TUI Tab for Accessibility Scanner."""

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("Accessibility Scanner (HTML, JSX, Vue)", classes="tab-title")

            with Horizontal(classes="input-group"):
                yield Label("Directory:")
                yield Input(id="a11y_dir_input", value=".", placeholder="Project Directory")

            with Horizontal(classes="input-group"):
                yield Label("File Pattern:")
                yield Input(id="a11y_pattern_input", value="", placeholder="e.g. *.html (optional)")

            with Horizontal(classes="input-group"):
                yield Label("Ignore:")
                yield Input(id="a11y_ignore_input", value="", placeholder="e.g. node_modules,dist (comma separated)")

            with Horizontal(classes="button-group"):
                yield Button("Scan for Violations", id="a11y_scan_btn", variant="primary")

            yield DataTable(id="a11y_table")

    def on_mount(self) -> None:
        table = self.query_one("#a11y_table", DataTable)
        table.add_columns("File", "Line", "Severity", "Rule ID", "Message")

    @on(Button.Pressed, "#a11y_scan_btn")
    def run_scan(self) -> None:
        dir_val = self.query_one("#a11y_dir_input", Input).value.strip() or "."
        pattern_val = self.query_one("#a11y_pattern_input", Input).value.strip()
        ignore_val = self.query_one("#a11y_ignore_input", Input).value.strip()

        table = self.query_one("#a11y_table", DataTable)
        table.clear()

        project_dir = Path(dir_val).resolve()

        ignore_patterns = [p.strip() for p in ignore_val.split(",")] if ignore_val else []
        if not ignore_patterns:
            ignore_patterns = [".git*", "node_modules*", "dist*", "build*", ".next*"]

        file_pattern = pattern_val if pattern_val else None

        try:
            scanner = AccessibilityScanner(project_dir, file_pattern, ignore_patterns)
            scanner.scan()

            if not scanner.violations:
                self.app.notify("✅ No accessibility violations found.", title="Success")
                return

            # Sort violations
            scanner.violations.sort(key=lambda x: (x.severity != "ERROR", x.file, x.lineno))

            for v in scanner.violations:
                table.add_row(v.file, str(v.lineno), v.severity, v.rule_id, v.message)

            self.app.notify(f"Found {len(scanner.violations)} violation(s).", severity="warning", title="Scan Complete")

        except Exception as e:
            self.app.notify(f"Error scanning: {e}", severity="error", title="Error")
