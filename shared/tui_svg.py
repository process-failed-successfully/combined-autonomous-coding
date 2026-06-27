import re
import xml.etree.ElementTree as ET
from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Static, Input, Button, Label, Markdown, TabPane
from textual.containers import Vertical, Horizontal

class SvgLabTab(TabPane):
    """A TUI tab for SVG operations."""

    def __init__(self, project_dir: Path = None):
        super().__init__("SVG Lab", id="tab-svg")
        self.project_dir = project_dir or Path(".")

    def compose(self) -> ComposeResult:
        with Vertical(classes="p-4"):
            yield Label("SVG Lab: Validate and Minify SVGs", classes="text-xl text-bold mb-4")

            with Horizontal(classes="mb-4 gap-2"):
                yield Input(placeholder="Path to SVG file...", id="svg-file-input")

            with Horizontal(classes="mb-4 gap-2"):
                yield Button("Validate", id="svg-validate-btn", variant="primary")
                yield Button("Minify", id="svg-minify-btn", variant="warning")

            yield Static("Results:", classes="text-bold mb-2")
            yield Markdown("*(Output will appear here)*", id="svg-output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        file_input = self.query_one("#svg-file-input", Input).value.strip()
        output_widget = self.query_one("#svg-output", Markdown)

        if not file_input:
            output_widget.update("**Error:** Please provide an SVG file path.")
            return

        filepath = Path(file_input)
        if not filepath.exists() or not filepath.is_file():
            output_widget.update(f"**Error:** File not found: `{filepath}`")
            return

        if event.button.id == "svg-validate-btn":
            try:
                tree = ET.parse(filepath)
                root = tree.getroot()
                if "svg" in root.tag.lower():
                    output_widget.update(f"✅ **Valid SVG!**\n\nRoot tag: `{root.tag}`")
                else:
                    output_widget.update(f"❌ **Invalid SVG!**\n\nRoot tag `{root.tag}` is not `<svg>`.")
            except Exception as e:
                output_widget.update(f"❌ **XML Parse Error:**\n\n`{e}`")

        elif event.button.id == "svg-minify-btn":
            try:
                content = filepath.read_text(encoding="utf-8")
                original_size = len(content)

                minified = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
                minified = re.sub(r'>\s+<', '><', minified)
                minified = re.sub(r'\s{2,}', ' ', minified)
                minified = minified.strip()

                new_size = len(minified)
                filepath.write_text(minified, encoding="utf-8")

                savings = original_size - new_size
                pct = (savings / original_size * 100) if original_size > 0 else 0

                output_widget.update(
                    f"✅ **Minified SVG successfully!**\n\n"
                    f"- Original size: `{original_size}` bytes\n"
                    f"- New size: `{new_size}` bytes\n"
                    f"- Savings: `{savings}` bytes ({pct:.1f}%)"
                )
            except Exception as e:
                output_widget.update(f"❌ **Minification Error:**\n\n`{e}`")
