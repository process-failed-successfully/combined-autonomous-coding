from pathlib import Path
import asyncio
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, RichLog, TabbedContent, TabPane
from textual.containers import Container, Vertical, Horizontal
from textual import on
from shared.cert_lab import CertLabManager

class CertLabTab(Container):
    """
    Certificate Laboratory Tab.
    inspects local/remote certificates and generates self-signed certificates.
    """

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = CertLabManager()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Certificate Laboratory[/bold]", classes="welcome-text")

            with TabbedContent():
                with TabPane("Inspect"):
                    with Vertical():
                        yield Label("Target (File Path or Host:Port):")
                        with Horizontal(classes="stat-box"):
                            yield Input(placeholder="e.g. google.com or ./cert.pem", id="cert-target")
                            yield Button("Inspect", id="btn-cert-inspect", variant="primary")

                        yield Label("[bold]Certificate Details[/bold]")
                        yield RichLog(id="cert-inspect-log", wrap=True, highlight=True, markup=True)

                with TabPane("Generate"):
                    with Vertical():
                        yield Label("[bold]Generate Self-Signed Certificate[/bold]")

                        with Vertical(classes="stat-box"):
                            yield Label("Common Name (CN):")
                            yield Input(placeholder="e.g. localhost", id="cert-cn")

                            yield Label("Subject Alternative Names (SANs, comma-separated):")
                            yield Input(placeholder="e.g. localhost, 127.0.0.1", id="cert-sans")

                            yield Label("Validity (Days):")
                            yield Input(placeholder="365", value="365", id="cert-days", type="integer")

                            yield Button("Generate", id="btn-cert-generate", variant="success")

                        yield Label("[bold]Output[/bold]")
                        yield RichLog(id="cert-gen-log", wrap=True, highlight=True, markup=True)

    @on(Button.Pressed, "#btn-cert-inspect")
    async def on_inspect(self) -> None:
        target = self.query_one("#cert-target", Input).value.strip()
        if not target:
            self.notify("Target required.", severity="error")
            return

        log = self.query_one("#cert-inspect-log", RichLog)
        log.clear()
        log.write(f"Inspecting {target}...")

        try:
            # Determine if file or host
            path = Path(target)
            if path.exists() and path.is_file():
                log.write(f"Reading local file: {path}")
                details = await asyncio.to_thread(self.manager.inspect_file, path)
            else:
                # Host
                host = target
                port = 443
                if ":" in target:
                    parts = target.split(":")
                    host = parts[0]
                    if len(parts) > 1 and parts[1].isdigit():
                        port = int(parts[1])

                log.write(f"Connecting to {host}:{port}...")
                details = await asyncio.to_thread(self.manager.inspect_host, host, port)

            # Render details
            self._render_details(log, details)

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Inspection failed: {e}", severity="error")

    def _render_details(self, log: RichLog, details: dict) -> None:
        log.write("\n[bold underline]Certificate Info[/bold underline]")

        # Subject
        log.write("[bold]Subject:[/bold]")
        for k, v in details.get("Subject", {}).items():
            log.write(f"  {k}: [cyan]{v}[/cyan]")

        # Issuer
        log.write("\n[bold]Issuer:[/bold]")
        for k, v in details.get("Issuer", {}).items():
            log.write(f"  {k}: [blue]{v}[/blue]")

        # Dates
        log.write(f"\n[bold]Not Before:[/bold] {details.get('Not Before')}")
        log.write(f"[bold]Not After:[/bold]  {details.get('Not After')}")

        days = details.get("Days Remaining", 0)
        color = "green" if days > 30 else "yellow" if days > 0 else "red"
        log.write(f"[bold]Days Remaining:[/bold] [{color}]{days}[/{color}]")

        # SANs
        sans = details.get("SANs", [])
        log.write(f"\n[bold]SANs:[/bold] {', '.join(sans) if sans else 'None'}")

        # Misc
        log.write(f"\n[bold]Serial:[/bold] {details.get('Serial Number')}")
        log.write(f"[bold]Fingerprint:[/bold] {details.get('Fingerprint (SHA256)')}")

    @on(Button.Pressed, "#btn-cert-generate")
    async def on_generate(self) -> None:
        cn = self.query_one("#cert-cn", Input).value.strip()
        sans_str = self.query_one("#cert-sans", Input).value.strip()
        days_str = self.query_one("#cert-days", Input).value.strip()

        if not cn:
            self.notify("Common Name required.", severity="error")
            return

        try:
            days = int(days_str)
        except ValueError:
            self.notify("Invalid days value.", severity="error")
            return

        sans = [s.strip() for s in sans_str.split(",") if s.strip()]
        # Ensure CN is in SANs
        if cn not in sans:
            sans.insert(0, cn)

        log = self.query_one("#cert-gen-log", RichLog)
        log.clear()
        log.write(f"Generating certificate for [cyan]{cn}[/cyan]...")

        try:
            output_dir = self.project_dir

            def do_gen():
                return self.manager.generate_self_signed(cn, sans, days, output_dir)

            cert_path, key_path = await asyncio.to_thread(do_gen)

            log.write("[bold green]Success![/bold green]")
            log.write(f"Certificate: {cert_path}")
            log.write(f"Private Key: {key_path}")

            self.notify("Certificate generated.")

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {e}")
            self.notify(f"Generation failed: {e}", severity="error")
