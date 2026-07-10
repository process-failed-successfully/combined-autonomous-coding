from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Static, RichLog
from textual.containers import Container, Horizontal, Vertical
from textual import on
from shared.cron2systemd_lab import Cron2SystemdManager

class Cron2SystemdTab(Container):
    """Tab for converting Cron to Systemd units."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.manager = Cron2SystemdManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Cron to Systemd Lab[/bold]", classes="welcome-text")

            with Vertical(classes="stat-box"):
                yield Label("Cron Line (e.g. '0 5 * * * root /opt/backup.sh'):")
                with Horizontal():
                    yield Input(placeholder="min hour dom mon dow [user] command", id="input-c2s-cron")
                    yield Button("Convert", id="btn-c2s-convert", variant="primary")

                yield Label("Name (optional, defaults to 'cronjob'):")
                yield Input(placeholder="backup-job", id="input-c2s-name")

            with Horizontal():
                with Vertical(classes="stat-box"):
                    yield Label("[bold].service[/bold]")
                    yield RichLog(id="log-c2s-service", wrap=True, highlight=True, markup=True)

                with Vertical(classes="stat-box"):
                    yield Label("[bold].timer[/bold]")
                    yield RichLog(id="log-c2s-timer", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-c2s-convert")
    def on_convert(self) -> None:
        cron_line = self.query_one("#input-c2s-cron", Input).value
        name = self.query_one("#input-c2s-name", Input).value or "cronjob"

        log_service = self.query_one("#log-c2s-service", RichLog)
        log_timer = self.query_one("#log-c2s-timer", RichLog)

        log_service.clear()
        log_timer.clear()

        if not cron_line:
            self.notify("Cron line is required.", severity="error")
            return

        try:
            service_content, timer_content = self.manager.generate_files(name, cron_line)
            log_service.write(service_content)
            log_timer.write(timer_content)
            self.notify("Converted successfully!")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            log_service.write(f"[red]Error parsing cron line: {e}[/red]")
