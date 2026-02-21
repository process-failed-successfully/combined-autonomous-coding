import asyncio
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Label, Button, DataTable, Input, RichLog, TextArea, TabbedContent, TabPane
from textual import on
from shared.email_lab import EmailLabManager

class EmailLabTab(Container):
    """Tab for Email Lab (SMTP Server & Viewer)."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = EmailLabManager(project_dir)
        self.server_task = None
        self.is_server_running = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Email Lab (SMTP)[/bold]", classes="welcome-text")

            # Server Control
            with Horizontal(classes="stat-box"):
                yield Label("SMTP Port:", classes="label")
                yield Input(placeholder="1025", value="1025", id="email-port-input", type="integer")
                yield Button("Start Server", id="btn-email-start", variant="primary")
                yield Button("Stop Server", id="btn-email-stop", variant="error", disabled=True)
                yield Label("Status: Stopped", id="lbl-email-status")

            with TabbedContent():
                with TabPane("Inbox"):
                    with Horizontal():
                        # Left: List
                        with Vertical(id="email-list-container", classes="stat-box"):
                            yield Label("[bold]Inbox[/bold]")
                            yield DataTable(id="email-table")
                            with Horizontal():
                                yield Button("Refresh", id="btn-email-refresh", variant="default")
                                yield Button("Clear History", id="btn-email-clear", variant="warning")

                        # Right: Viewer
                        with Vertical(id="email-view-container", classes="stat-box"):
                            yield Label("[bold]Email Details[/bold]")
                            yield RichLog(id="email-view-log", wrap=True, highlight=True, markup=True)

                with TabPane("Send Test"):
                    with Vertical(classes="stat-box"):
                        yield Label("From:")
                        yield Input(placeholder="sender@example.com", value="test@example.com", id="email-send-from")
                        yield Label("To (comma separated):")
                        yield Input(placeholder="recipient@example.com", value="user@example.com", id="email-send-to")
                        yield Label("Subject:")
                        yield Input(placeholder="Test Subject", value="Hello from Email Lab", id="email-send-subject")
                        yield Label("Body:")
                        yield TextArea(id="email-send-body", language="markdown")

                        # Server Settings for Sending
                        with Horizontal():
                            yield Label("Target Host:")
                            yield Input(value="127.0.0.1", id="email-send-host")
                            yield Label("Target Port:")
                            yield Input(value="1025", id="email-send-port")

                        yield Button("Send Email", id="btn-email-send", variant="success")

    def on_mount(self) -> None:
        table = self.query_one("#email-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Time", "From", "To", "Subject")
        self.refresh_inbox()

    @on(Button.Pressed, "#btn-email-start")
    async def start_server(self):
        port_str = self.query_one("#email-port-input", Input).value
        port = int(port_str) if port_str else 1025

        if self.is_server_running:
            return

        self.query_one("#lbl-email-status").update(f"Status: Starting on {port}...")

        # Start background task
        self.server_task = asyncio.create_task(self.manager.start_server(port))
        self.is_server_running = True

        self.query_one("#btn-email-start").disabled = True
        self.query_one("#btn-email-stop").disabled = False
        self.query_one("#lbl-email-status").update(f"Status: [green]Running on {port}[/green]")
        self.notify(f"SMTP Server started on port {port}")

    @on(Button.Pressed, "#btn-email-stop")
    async def stop_server(self):
        if not self.is_server_running or not self.server_task:
            return

        self.server_task.cancel()
        try:
            await self.server_task
        except asyncio.CancelledError:
            pass

        self.is_server_running = False
        self.server_task = None

        self.query_one("#btn-email-start").disabled = False
        self.query_one("#btn-email-stop").disabled = True
        self.query_one("#lbl-email-status").update("Status: Stopped")
        self.notify("SMTP Server stopped")

    @on(Button.Pressed, "#btn-email-refresh")
    def refresh_inbox(self):
        table = self.query_one("#email-table", DataTable)
        table.clear()

        emails = self.manager.get_emails(limit=50) # Get last 50
        for email in reversed(emails): # Newest first
            to_str = ", ".join(email['recipients'])
            table.add_row(
                email['id'],
                email['timestamp'],
                email['sender'],
                to_str,
                email['subject'],
                key=email['id']
            )

    @on(Button.Pressed, "#btn-email-clear")
    def clear_inbox(self):
        self.manager.clear_history()
        self.refresh_inbox()
        self.query_one("#email-view-log", RichLog).clear()
        self.notify("Inbox cleared.")

    @on(DataTable.RowSelected, "#email-table")
    def on_email_selected(self, event: DataTable.RowSelected):
        req_id = event.row_key.value
        self.show_email(req_id)

    def show_email(self, req_id: str):
        email_data = self.manager.get_email(req_id)
        log = self.query_one("#email-view-log", RichLog)
        log.clear()

        if not email_data:
            log.write("[red]Email not found.[/red]")
            return

        log.write(f"[bold]Subject:[/bold] {email_data['subject']}")
        log.write(f"[bold]From:[/bold]    {email_data['sender']}")
        log.write(f"[bold]To:[/bold]      {', '.join(email_data['recipients'])}")
        log.write(f"[dim]Time:      {email_data['timestamp']}[/dim]")
        log.write("-" * 40)
        log.write(email_data['content'])

    @on(Button.Pressed, "#btn-email-send")
    async def send_test_email(self):
        sender = self.query_one("#email-send-from", Input).value
        to_str = self.query_one("#email-send-to", Input).value
        subject = self.query_one("#email-send-subject", Input).value
        body = self.query_one("#email-send-body", TextArea).text

        host = self.query_one("#email-send-host", Input).value
        port_str = self.query_one("#email-send-port", Input).value
        port = int(port_str) if port_str else 1025

        recipients = [r.strip() for r in to_str.split(",") if r.strip()]

        if not sender or not recipients:
            self.notify("Sender and Recipients required.", severity="error")
            return

        self.notify("Sending email...")
        self.query_one("#btn-email-send").disabled = True

        try:
            # Run blocking send in thread
            await asyncio.to_thread(
                self.manager.send_email,
                host, port, sender, recipients, subject, body
            )
            self.notify("Email sent successfully.")

            # Auto-refresh if sending to self (localhost)
            if "127.0.0.1" in host or "localhost" in host:
                self.set_timer(0.5, self.refresh_inbox)
        except Exception as e:
            self.notify(f"Error sending email: {e}", severity="error")
        finally:
            self.query_one("#btn-email-send").disabled = False
