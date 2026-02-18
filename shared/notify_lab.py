import sys
import subprocess
import requests
import platform
import shutil
from typing import Optional, List, Dict
from pathlib import Path
from rich.console import Console
from shared.config_loader import load_config_from_file

console = Console()

class NotifyLabManager:
    """
    Manages sending notifications to various channels.
    """
    def __init__(self, slack_url: Optional[str] = None, discord_url: Optional[str] = None):
        # Attempt to load from config if not provided
        self.config = load_config_from_file() or {}

        self.slack_url = slack_url or self.config.get("slack_webhook_url")
        self.discord_url = discord_url or self.config.get("discord_webhook_url")

    def send_desktop(self, title: str, message: str) -> bool:
        """
        Sends a desktop notification using OS-specific tools.
        """
        system = platform.system().lower()
        title = title or "Notify Lab"

        try:
            if system == "linux":
                if shutil.which("notify-send"):
                    subprocess.run(["notify-send", title, message], check=True)
                    return True
                else:
                    console.print("[yellow]notify-send not found. Desktop notifications disabled.[/yellow]")

            elif system == "darwin": # macOS
                # Escape quotes for AppleScript
                safe_msg = message.replace('"', '\\"')
                safe_title = title.replace('"', '\\"')
                script = f'display notification "{safe_msg}" with title "{safe_title}"'
                subprocess.run(["osascript", "-e", script], check=True)
                return True

            elif system == "windows":
                # Try PowerShell
                # Requires >= Windows 10 for BurntToast or custom script using System.Windows.Forms
                # Simple msg * "message" works on some versions but is modal
                # Let's try a simple PowerShell balloon tip script
                ps_script = f"""
                [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
                $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon
                $objNotifyIcon.Icon = [System.Drawing.Icon]::ExtractAssociatedIcon((Get-Process -id $pid).Path)
                $objNotifyIcon.BalloonTipIcon = "Info"
                $objNotifyIcon.BalloonTipText = "{message}"
                $objNotifyIcon.BalloonTipTitle = "{title}"
                $objNotifyIcon.Visible = $True
                $objNotifyIcon.ShowBalloonTip(10000)
                """
                # This might be too heavy and requires non-headless execution.
                # Just warn for now.
                console.print("[yellow]Windows desktop notifications not fully supported yet.[/yellow]")
                return False

            else:
                console.print(f"[yellow]Desktop notifications not supported on {system}.[/yellow]")

        except Exception as e:
            console.print(f"[red]Failed to send desktop notification: {e}[/red]")
            return False

        return False

    def send_slack(self, message: str) -> bool:
        """Sends a notification to Slack."""
        if not self.slack_url:
            console.print("[yellow]Slack webhook URL not configured.[/yellow]")
            return False

        try:
            payload = {"text": message}
            resp = requests.post(self.slack_url, json=payload, timeout=5)
            resp.raise_for_status()
            console.print("[green]Slack notification sent.[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to send Slack notification: {e}[/red]")
            return False

    def send_discord(self, message: str) -> bool:
        """Sends a notification to Discord."""
        if not self.discord_url:
            console.print("[yellow]Discord webhook URL not configured.[/yellow]")
            return False

        try:
            payload = {"content": message}
            resp = requests.post(self.discord_url, json=payload, timeout=5)
            resp.raise_for_status()
            console.print("[green]Discord notification sent.[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to send Discord notification: {e}[/red]")
            return False

def run_notify_lab_logic(args):
    """
    CLI Entry point for Notify Lab.
    """
    manager = NotifyLabManager(
        slack_url=args.slack_url,
        discord_url=args.discord_url
    )

    message = args.message
    if not message:
        # Read from stdin if available
        if not sys.stdin.isatty():
            message = sys.stdin.read().strip()

    if not message:
        console.print("[red]Error: Message required (argument or stdin).[/red]")
        sys.exit(1)

    targets = args.to
    if not targets:
        # Default to console only if no targets specified?
        # Actually, let's default to desktop if available, else just console log.
        # But 'notify' command implies action.
        # Let's verify 'to' arguments.
        # If user runs `notify "hello"`, they probably want desktop + console.
        targets = ["desktop"]

    success_count = 0

    if "desktop" in targets or "all" in targets:
        if manager.send_desktop(args.title, message):
            success_count += 1

    if "slack" in targets or "all" in targets:
        if manager.send_slack(message):
            success_count += 1

    if "discord" in targets or "all" in targets:
        if manager.send_discord(message):
            success_count += 1

    if "console" in targets or "all" in targets:
        # Just print it nicely
        title_part = f"[bold]{args.title}[/bold]: " if args.title else ""
        console.print(f"🔔 {title_part}{message}")
        success_count += 1

    if success_count == 0:
        sys.exit(1)
