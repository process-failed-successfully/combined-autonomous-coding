import asyncio
import json
import time
import sys
import email
import email.policy
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

class SmtpProtocol(asyncio.Protocol):
    """
    Minimal SMTP Server Protocol implementation using asyncio.
    Handles basic commands: HELO, EHLO, MAIL, RCPT, DATA, QUIT, RSET, NOOP.
    """
    def __init__(self, manager):
        self.manager = manager
        self.transport = None
        self.peername = None
        self.buffer = b""
        self.state = "COMMAND" # COMMAND or DATA
        self.envelope_from = ""
        self.envelope_to = []
        self.data_buffer = []

    def connection_made(self, transport):
        self.transport = transport
        self.peername = transport.get_extra_info('peername')
        # print(f"Connection from {self.peername}")
        self.send_response(220, "Email Lab SMTP Server Ready")

    def data_received(self, data):
        self.buffer += data

        if self.state == "DATA":
            self.handle_data_chunk()
        else:
            self.handle_command_chunk()

    def handle_command_chunk(self):
        while b"\r\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\r\n", 1)
            line = line.decode('utf-8', errors='replace').strip()
            if not line:
                continue
            self.process_command(line)

    def handle_data_chunk(self):
        # Look for the end of data marker: \r\n.\r\n
        # But we might receive it in chunks.
        # Simplest way: check if buffer contains the marker.
        # Note: The marker might be split across chunks.
        # Since this is a lab tool, we can be a bit lenient or just look for the sequence in the buffer.

        # We need to handle transparency: lines starting with .. -> .
        # But for now let's just look for the terminator.

        if b"\r\n.\r\n" in self.buffer:
            data_content, self.buffer = self.buffer.split(b"\r\n.\r\n", 1)
            self.data_buffer.append(data_content)
            full_data = b"".join(self.data_buffer)
            self.process_data_complete(full_data)
            self.state = "COMMAND"
            self.data_buffer = []
            self.send_response(250, "OK Message accepted")

        # Optimization: if buffer gets too large without terminator, we could move it to data_buffer
        # to keep self.buffer small, but for now we just keep appending.
        # Actually, let's play safe and check if buffer ends with \r\n. if not, wait.
        pass

    def process_command(self, line):
        parts = line.split(None, 1)
        cmd = parts[0].upper()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ["HELO", "EHLO"]:
            self.envelope_from = ""
            self.envelope_to = []
            self.send_response(250, f"Hello {arg or 'client'}")

        elif cmd == "MAIL":
            # MAIL FROM:<sender>
            # Basic parsing
            if ":" in line:
                self.envelope_from = line.split(":", 1)[1].strip().strip("<>")
            self.send_response(250, "OK")

        elif cmd == "RCPT":
            # RCPT TO:<recipient>
            if ":" in line:
                rcpt = line.split(":", 1)[1].strip().strip("<>")
                self.envelope_to.append(rcpt)
            self.send_response(250, "OK")

        elif cmd == "DATA":
            self.state = "DATA"
            self.data_buffer = [] # Clear previous data
            # Check if we have any data in buffer that came after DATA command immediately?
            # Usually client waits for 354.
            self.send_response(354, "End data with <CR><LF>.<CR><LF>")

        elif cmd == "QUIT":
            self.send_response(221, "Bye")
            self.transport.close()

        elif cmd == "RSET":
            self.envelope_from = ""
            self.envelope_to = []
            self.data_buffer = []
            self.state = "COMMAND"
            self.send_response(250, "OK")

        elif cmd == "NOOP":
            self.send_response(250, "OK")

        else:
            self.send_response(500, "Command not recognized")

    def process_data_complete(self, data_bytes):
        # Handle transparency (unescape dots)
        # In SMTP, a line starting with '.' has an extra '.' prepended.
        # We should replace b'\r\n..' with b'\r\n.'
        # But for this simple implementation, let's assume standard clients.

        content = data_bytes.decode('utf-8', errors='replace')

        # Log to manager
        self.manager.log_email(
            self.envelope_from,
            self.envelope_to,
            content
        )

    def send_response(self, code, message):
        response = f"{code} {message}\r\n".encode('utf-8')
        if self.transport:
            self.transport.write(response)

class EmailLabManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.history_file = project_dir / ".email_history.jsonl"
        self.console = Console()

    async def start_server(self, port: int):
        loop = asyncio.get_running_loop()
        server = await loop.create_server(
            lambda: SmtpProtocol(self),
            '127.0.0.1',
            port
        )

        self.console.print(f"[bold green]Email Lab SMTP Server listening on 127.0.0.1:{port}...[/bold green]")
        self.console.print(f"[dim]Saving emails to: {self.history_file}[/dim]")
        self.console.print("Press Ctrl+C to stop.\n")

        async with server:
            await server.serve_forever()

    def log_email(self, sender, recipients, content):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        req_id = hex(int(time.time() * 1000))[2:]

        # Parse email to get subject for logging
        try:
            msg = email.message_from_string(content)
            subject = msg.get('subject', '(No Subject)')
        except:
            subject = "(Parse Error)"

        entry = {
            "id": req_id,
            "timestamp": timestamp,
            "sender": sender,
            "recipients": recipients,
            "content": content,
            "subject": subject
        }

        # Console Output
        self.console.print(f"[bold]New Email[/bold] (ID: {req_id})")
        self.console.print(f"  From: {sender}")
        self.console.print(f"  To:   {', '.join(recipients)}")
        self.console.print(f"  Subj: {subject}")

        # Save to file
        try:
            with open(self.history_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            self.console.print(f"[red]Error saving email: {e}[/red]")

    def get_emails(self, limit: int = 10) -> List[Dict]:
        if not self.history_file.exists():
            return []

        entries = []
        try:
            with open(self.history_file, 'r') as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))
        except Exception:
            return []

        return entries[-limit:]

    def get_email(self, req_id: str) -> Optional[Dict]:
        if not self.history_file.exists():
            return None

        try:
            with open(self.history_file, 'r') as f:
                for line in f:
                    if line.strip():
                        e = json.loads(line)
                        if e['id'] == req_id:
                            return e
        except Exception:
            pass
        return None

    def list_emails(self, limit: int = 10):
        entries = self.get_emails(limit)
        if not entries:
            self.console.print("No email history found.")
            return

        table = Table(title=f"Recent Emails (Last {len(entries)})")
        table.add_column("ID", style="cyan")
        table.add_column("Time", style="dim")
        table.add_column("From")
        table.add_column("To")
        table.add_column("Subject", style="bold")

        for e in entries:
            to_str = ", ".join(e['recipients'])
            if len(to_str) > 20:
                to_str = to_str[:17] + "..."

            table.add_row(
                e['id'],
                e['timestamp'],
                e['sender'],
                to_str,
                e['subject']
            )

        self.console.print(table)

    def show_email(self, req_id: str):
        target = self.get_email(req_id)

        if not target:
            self.console.print(f"[red]Email {req_id} not found.[/red]")
            return

        self.console.print(f"[bold]Email Details: {req_id}[/bold]")
        self.console.print(f"Time: {target['timestamp']}")
        self.console.print(f"From: {target['sender']}")
        self.console.print(f"To:   {', '.join(target['recipients'])}")
        self.console.print(f"Subject: {target['subject']}")
        self.console.print("-" * 40)

        # Parse content to show body better
        try:
            msg = email.message_from_string(target['content'])
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition'))

                    if ctype == 'text/plain' and 'attachment' not in cdispo:
                        self.console.print(part.get_payload(decode=True).decode('utf-8', errors='replace'))
                        break # Only show first text part
            else:
                self.console.print(msg.get_payload(decode=True).decode('utf-8', errors='replace'))
        except Exception as e:
            self.console.print(f"[red]Error parsing content: {e}[/red]")
            self.console.print(target['content'])

    def clear_history(self):
        if self.history_file.exists():
            self.history_file.unlink()
            self.console.print("✅ Email history cleared.")
        else:
            self.console.print("History is already empty.")

    def send_email(self, host: str, port: int, sender: str, recipients: List[str], subject: str, body: str):
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ", ".join(recipients)

        try:
            with smtplib.SMTP(host, port) as server:
                server.send_message(msg)
            self.console.print(f"✅ Email sent to {', '.join(recipients)}")
        except Exception as e:
            self.console.print(f"[red]Error sending email: {e}[/red]")
            raise e

async def run_email_lab_logic(args):
    """
    CLI Entry point for Email Lab.
    """
    project_dir = args.project_dir.resolve()
    manager = EmailLabManager(project_dir)

    if args.action in ["server", "serve"]:
        try:
            await manager.start_server(args.port)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error starting server: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "send":
        try:
            manager.send_email(
                host=args.host,
                port=args.port,
                sender=args.sender,
                recipients=args.to,
                subject=args.subject,
                body=args.body
            )
        except Exception:
            sys.exit(1)

    elif args.action == "list":
        manager.list_emails(args.limit)

    elif args.action == "show":
        manager.show_email(args.id)

    elif args.action == "clear":
        manager.clear_history()

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
