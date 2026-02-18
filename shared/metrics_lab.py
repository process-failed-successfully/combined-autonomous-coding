import sys
import requests
import re
from typing import List, Dict, Any, Optional, Generator

# Lazy import handling for prometheus_client
try:
    from prometheus_client.parser import text_string_to_metric_families
    from prometheus_client.core import GaugeMetricFamily, REGISTRY
    from prometheus_client import make_wsgi_app
    from wsgiref.simple_server import make_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

class SystemCollector:
    """Collects system metrics using MonitorLabManager."""

    def collect(self):
        # Lazy import to avoid startup overhead or circular deps
        from shared.monitor_lab import MonitorLabManager

        manager = MonitorLabManager()
        stats = manager.get_system_stats()

        # CPU
        yield GaugeMetricFamily('system_cpu_usage_percent', 'System CPU usage percentage', value=stats['cpu'])

        # Memory
        mem = GaugeMetricFamily('system_memory_usage_bytes', 'System memory usage', labels=['type'])
        mem.add_metric(['used'], stats['memory']['used'])
        mem.add_metric(['free'], stats['memory']['free'])
        mem.add_metric(['total'], stats['memory']['total'])
        yield mem

        # Disk
        disk = GaugeMetricFamily('system_disk_usage_bytes', 'System disk usage', labels=['type'])
        disk.add_metric(['used'], stats['disk']['used'])
        disk.add_metric(['free'], stats['disk']['free'])
        disk.add_metric(['total'], stats['disk']['total'])
        yield disk

class MetricsLabManager:
    """Manages metrics scraping, linting, and serving."""

    def __init__(self):
        try:
            from rich.console import Console
            from rich.table import Table
            self.Console = Console
            self.Table = Table
            self.console = Console()
        except ImportError:
            # Fallback or error
            print("Error: 'rich' library not found.", file=sys.stderr)
            sys.exit(1)

        if not PROMETHEUS_AVAILABLE:
            self.console.print("[red]Error: 'prometheus_client' library not found. Please install it.[/red]")
            sys.exit(1)

    def scrape(self, url: str, filter_pattern: Optional[str] = None):
        """Scrapes metrics from a URL and displays them."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            families = list(text_string_to_metric_families(response.text))

            table = self.Table(title=f"Metrics from {url}")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Labels", style="yellow")
            table.add_column("Value", justify="right")

            count = 0
            for family in families:
                if filter_pattern and filter_pattern not in family.name:
                    continue

                for sample in family.samples:
                    name, labels, value = sample.name, sample.labels, sample.value

                    # Basic label formatting
                    label_str = ", ".join([f"{k}={v}" for k, v in labels.items()])

                    table.add_row(name, family.type, label_str, str(value))
                    count += 1

            if count == 0:
                self.console.print("[yellow]No metrics found matching filter.[/yellow]")
            else:
                self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error scraping metrics: {e}[/red]")
            sys.exit(1)

    def lint(self, url: str):
        """Lints metrics exposed at a URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            lines = response.text.splitlines()
            families = list(text_string_to_metric_families(response.text))

            errors = []
            warnings = []

            # 1. Check for HELP and TYPE lines
            seen_help = set()
            seen_type = set()

            for line in lines:
                if line.startswith('# HELP'):
                    parts = line.split()
                    if len(parts) >= 3:
                        seen_help.add(parts[2])
                elif line.startswith('# TYPE'):
                    parts = line.split()
                    if len(parts) >= 3:
                        seen_type.add(parts[2])

            for family in families:
                if family.name not in seen_help:
                    warnings.append(f"Missing HELP for metric '{family.name}'")
                if family.name not in seen_type:
                    warnings.append(f"Missing TYPE for metric '{family.name}'")

                # 2. Check naming conventions
                if family.type == 'counter' and not family.name.endswith('_total'):
                    errors.append(f"Counter '{family.name}' MUST end with '_total'")

            if errors:
                self.console.print("[red]Errors:[/red]")
                for e in errors:
                    self.console.print(f"  - {e}")

            if warnings:
                self.console.print("[yellow]Warnings:[/yellow]")
                for w in warnings:
                    self.console.print(f"  - {w}")

            if not errors and not warnings:
                self.console.print("[green]✅ Metrics look good![/green]")
            elif errors:
                sys.exit(1)

        except Exception as e:
            self.console.print(f"[red]Error linting metrics: {e}[/red]")
            sys.exit(1)

    def serve(self, port: int):
        """Serves system metrics on the specified port."""
        try:
            # Register our custom collector
            REGISTRY.register(SystemCollector())

            app = make_wsgi_app()
            httpd = make_server('', port, app)

            self.console.print(f"[green]Serving system metrics at http://0.0.0.0:{port}/metrics[/green]")
            self.console.print("Press Ctrl+C to stop.")
            httpd.serve_forever()

        except KeyboardInterrupt:
            self.console.print("\nStopped.")
        except Exception as e:
            self.console.print(f"[red]Error serving metrics: {e}[/red]")
            sys.exit(1)

def run_metrics_lab_logic(args):
    """CLI logic for Metrics Lab."""
    manager = MetricsLabManager()

    if args.action == "scrape":
        manager.scrape(args.url, args.filter)
    elif args.action == "lint":
        manager.lint(args.url)
    elif args.action == "serve":
        manager.serve(args.port)
    else:
        print(f"Unknown action: {args.action}")
        sys.exit(1)
