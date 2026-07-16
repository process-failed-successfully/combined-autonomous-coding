from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Label, TextArea, Select, OptionList
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual import on

from shared.crontab_lab import CrontabLabManager

class CrontabLabTab(Container):
    """Tab for managing system crontabs."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = CrontabLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Crontab Lab[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Load Current", id="btn-crontab-load", variant="primary")
                yield Button("Save Changes", id="btn-crontab-save", variant="success")
                yield Button("Clear Crontab", id="btn-crontab-clear", variant="error")
                yield Button("Backup Current", id="btn-crontab-backup", variant="warning")

            with Container(classes="stat-box"):
                yield Label("Crontab Editor:")
                yield TextArea(id="crontab-editor", language="bash", show_line_numbers=True)

            with Vertical(classes="stat-box"):
                yield Label("[bold]Backups[/bold]")
                with Horizontal():
                    yield Button("Refresh List", id="btn-crontab-refresh-backups", variant="primary")
                    yield Button("Restore Selected", id="btn-crontab-restore", variant="success")
                yield OptionList(id="crontab-backups-list")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.load_crontab()
        self.refresh_backups()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-crontab-load":
            self.load_crontab()
        elif button_id == "btn-crontab-save":
            self.save_crontab()
        elif button_id == "btn-crontab-clear":
            self.clear_crontab()
        elif button_id == "btn-crontab-backup":
            self.backup_crontab()
        elif button_id == "btn-crontab-refresh-backups":
            self.refresh_backups()
        elif button_id == "btn-crontab-restore":
            self.restore_crontab()

    def load_crontab(self) -> None:
        editor = self.query_one("#crontab-editor", TextArea)
        try:
            content = self.manager.read_crontab()
            editor.text = content
            self.notify("Crontab loaded successfully.")
        except Exception as e:
            self.notify(f"Error loading crontab: {e}", severity="error")

    def save_crontab(self) -> None:
        editor = self.query_one("#crontab-editor", TextArea)
        try:
            self.manager.write_crontab(editor.text)
            self.notify("Crontab saved successfully.")
        except Exception as e:
            self.notify(f"Error saving crontab: {e}", severity="error")

    def clear_crontab(self) -> None:
        try:
            self.manager.clear_crontab()
            self.query_one("#crontab-editor", TextArea).text = ""
            self.notify("Crontab cleared.")
        except Exception as e:
            self.notify(f"Error clearing crontab: {e}", severity="error")

    def backup_crontab(self) -> None:
        try:
            filepath = self.manager.backup_crontab()
            self.notify(f"Crontab backed up to: {filepath}")
            self.refresh_backups()
        except Exception as e:
            self.notify(f"Error backing up crontab: {e}", severity="error")

    def refresh_backups(self) -> None:
        option_list = self.query_one("#crontab-backups-list", OptionList)
        option_list.clear_options()
        try:
            backups = self.manager.list_backups()
            for backup in backups:
                option_list.add_option(backup)
        except Exception as e:
            self.notify(f"Error listing backups: {e}", severity="error")

    def restore_crontab(self) -> None:
        option_list = self.query_one("#crontab-backups-list", OptionList)
        if option_list.highlighted is None:
            self.notify("Please select a backup to restore.", severity="warning")
            return

        try:
            option = option_list.get_option_at_index(option_list.highlighted)
            filepath = str(option.prompt)
            self.manager.restore_crontab(filepath)
            self.load_crontab()
            self.notify(f"Restored crontab from: {filepath}")
        except Exception as e:
            self.notify(f"Error restoring crontab: {e}", severity="error")
