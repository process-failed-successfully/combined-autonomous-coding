from pathlib import Path
from typing import List, Optional
import json
import io
import contextlib
import asyncio

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Button, DataTable, RichLog, Input, Select
from textual import on

from shared.i18n import I18nManager

class I18nTab(Container):
    """Tab for managing Internationalization (translations)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = I18nManager(project_dir)
        self.source_file: Optional[Path] = None
        self.target_langs: List[str] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Internationalization Manager[/bold]", classes="welcome-text")

            # Configuration
            with Horizontal(classes="stat-box"):
                with Vertical():
                    yield Label("Source File:")
                    yield Input(placeholder="locales/en.json", id="i18n-source-input", value="locales/en.json")

                with Vertical():
                    yield Label("Target Languages (comma-separated):")
                    yield Input(placeholder="es, fr, de", id="i18n-langs-input")

                yield Button("Load", id="btn-i18n-load", variant="primary")

            # Actions
            with Horizontal(classes="stat-box"):
                yield Select.from_values(["gemini", "cursor", "local"], id="i18n-agent-select", value="gemini")
                yield Button("Verify", id="btn-i18n-verify", variant="warning", disabled=True)
                yield Button("Translate Missing", id="btn-i18n-translate", variant="success", disabled=True)

            # Data View
            with Vertical(id="i18n-data-container"):
                yield Label("[bold]Translation Grid[/bold]")
                yield DataTable(id="i18n-table")

            # Logs
            with Vertical(id="i18n-log-container", classes="stat-box"):
                yield Label("[bold]Logs[/bold]")
                yield RichLog(id="i18n-log", wrap=True, highlight=True, markup=True)

    def on_mount(self) -> None:
        table = self.query_one("#i18n-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Key", "Source Value", "Target Status")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-i18n-load":
            self.load_data()
        elif event.button.id == "btn-i18n-verify":
            self.verify_translations()
        elif event.button.id == "btn-i18n-translate":
            await self.translate_missing()

    def load_data(self) -> None:
        source_path_str = self.query_one("#i18n-source-input", Input).value
        langs_str = self.query_one("#i18n-langs-input", Input).value

        log = self.query_one("#i18n-log", RichLog)
        log.clear()

        if not source_path_str:
            self.notify("Source file path required.", severity="error")
            return

        self.source_file = self.project_dir / source_path_str
        if not self.source_file.exists():
            self.notify(f"File not found: {self.source_file}", severity="error")
            log.write(f"[red]File not found: {self.source_file}[/red]")
            return

        if not langs_str:
            self.notify("Target languages required.", severity="error")
            return

        self.target_langs = [l.strip() for l in langs_str.split(",") if l.strip()]

        # Load source content to display keys
        try:
            content = json.loads(self.source_file.read_text(encoding="utf-8"))
            keys = self.manager.flatten_keys(content)

            table = self.query_one("#i18n-table", DataTable)
            table.clear(columns=True)

            # Dynamic columns: Key, Source, Lang1, Lang2...
            cols = ["Key", "Source"] + self.target_langs
            table.add_columns(*cols)

            # Flatten content for display
            flat_content = self._flatten_dict(content)

            # Load target contents
            targets = {}
            for lang in self.target_langs:
                target_file = self.source_file.parent / f"{lang}.json"
                if target_file.exists():
                    try:
                        t_content = json.loads(target_file.read_text(encoding="utf-8"))
                        targets[lang] = self._flatten_dict(t_content)
                    except Exception:
                        targets[lang] = {}
                else:
                    targets[lang] = {}

            for key in keys:
                row = [key, str(flat_content.get(key, ""))]
                for lang in self.target_langs:
                    val = targets[lang].get(key)
                    if val is None:
                        row.append("[red]MISSING[/red]")
                    else:
                        row.append(str(val))

                table.add_row(*row)

            self.query_one("#btn-i18n-verify").disabled = False
            self.query_one("#btn-i18n-translate").disabled = False
            self.notify(f"Loaded {len(keys)} keys.")
            log.write(f"Loaded source: {self.source_file.name}")

        except Exception as e:
            self.notify(f"Error loading JSON: {e}", severity="error")
            log.write(f"[red]Error: {e}[/red]")

    def _flatten_dict(self, d: dict, parent_key: str = '') -> dict:
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self._flatten_dict(v, new_key))
            else:
                items[new_key] = v
        return items

    def verify_translations(self) -> None:
        if not self.source_file:
            return

        log = self.query_one("#i18n-log", RichLog)
        log.write("Verifying translations...")

        report = self.manager.verify(self.source_file, self.target_langs)

        if not report:
            log.write("[green]All translations are valid![/green]")
            self.notify("Verification passed.")
        else:
            log.write("[yellow]Issues found:[/yellow]")
            for lang, issues in report.items():
                log.write(f"[bold]{lang}[/bold]:")
                for issue in issues:
                    log.write(f"  - {issue}")
            self.notify("Issues found.", severity="warning")

    async def translate_missing(self) -> None:
        if not self.source_file:
            return

        agent_type = self.query_one("#i18n-agent-select", Select).value or "gemini"
        log = self.query_one("#i18n-log", RichLog)

        log.write(f"Translating missing keys with {agent_type}...")
        self.notify("Starting translation...")

        # Capture output
        capture = io.StringIO()
        success = False

        try:
            with contextlib.redirect_stdout(capture):
                success = await self.manager.translate(
                    self.source_file,
                    self.target_langs,
                    agent_type=agent_type
                )
        except Exception as e:
            capture.write(f"Error: {e}")

        output = capture.getvalue()
        log.write(output)

        if success:
            log.write("[green]Translation complete.[/green]")
            self.notify("Translation complete.")
            # Reload to show new values
            self.load_data()
        else:
            log.write("[red]Translation failed.[/red]")
            self.notify("Translation failed.", severity="error")
