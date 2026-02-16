import shutil
import subprocess  # nosec
import sys
from typing import List, Dict, Any, Optional


class DnsLabManager:
    """
    Manages DNS queries and diagnostics using `dig`.
    """
    def __init__(self):
        self.dig_path = shutil.which("dig")

    def run_command(self, cmd: List[str]) -> subprocess.CompletedProcess[str]:
        """
        Executes a shell command.
        """
        return subprocess.run(cmd, capture_output=True, text=True)  # nosec

    def lookup(self, domain: str, record_type: str = "A", server: Optional[str] = None) -> Dict[str, Any]:
        """
        Performs a DNS lookup for a specific record type.
        """
        if not self.dig_path:
            return {"error": "dig command not found. Please install dnsutils or bind-utils."}

        cmd = [self.dig_path, "+short", record_type, domain]
        if server:
            cmd.append(f"@{server}")

        try:
            result = self.run_command(cmd)
            if result.returncode != 0:
                return {"error": result.stderr.strip() or "Unknown error"}

            output = result.stdout.strip()
            if not output:
                return {"records": []}

            records = output.split('\n')
            return {"records": records}
        except Exception as e:
            return {"error": str(e)}

    def check_propagation(self, domain: str, record_type: str = "A") -> Dict[str, Any]:
        """
        Checks DNS propagation across multiple public DNS servers.
        """
        servers = {
            "Google": "8.8.8.8",
            "Cloudflare": "1.1.1.1",
            "Quad9": "9.9.9.9",
            "OpenDNS": "208.67.222.222"
        }

        results = {}
        for name, ip in servers.items():
            lookup_res = self.lookup(domain, record_type, server=ip)
            if "error" in lookup_res:
                results[name] = {"error": lookup_res["error"]}
            else:
                results[name] = lookup_res["records"]

        return results


def run_dns_lab_logic(args):
    """
    CLI entry point for DNS Lab.
    """
    manager = DnsLabManager()

    if not manager.dig_path:
        print("❌ Error: 'dig' command not found. Please install it (e.g., sudo apt install dnsutils).", file=sys.stderr)
        sys.exit(1)

    if args.action == "lookup":
        domain = args.domain
        record_type = args.type.upper()
        server = args.server

        print(f"--- DNS Lookup ({record_type}): {domain} ---")
        if server:
            print(f"Server: {server}")

        result = manager.lookup(domain, record_type, server)

        if "error" in result:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        records = result.get("records", [])
        if not records:
            print("No records found.")
        else:
            for r in records:
                print(f"  {r}")
        sys.exit(0)

    elif args.action == "propagation":
        domain = args.domain
        record_type = args.type.upper()

        print(f"--- DNS Propagation Check ({record_type}): {domain} ---")
        results = manager.check_propagation(domain, record_type)

        # Attempt to use rich for nicer output
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            table = Table(title=f"Propagation: {domain} ({record_type})")
            table.add_column("Provider", style="cyan")
            table.add_column("Server", style="magenta")
            table.add_column("Records", style="green")

            servers_ip = {
                "Google": "8.8.8.8",
                "Cloudflare": "1.1.1.1",
                "Quad9": "9.9.9.9",
                "OpenDNS": "208.67.222.222"
            }

            for provider, data in results.items():
                if isinstance(data, dict) and "error" in data:
                    table.add_row(provider, servers_ip.get(provider, ""), f"[red]Error: {data['error']}[/red]")
                else:
                    # data is list of records
                    records_str = "\n".join(data) if data else "[yellow]No records[/yellow]"
                    table.add_row(provider, servers_ip.get(provider, ""), records_str)

            console.print(table)

        except ImportError:
            # Fallback
            for provider, data in results.items():
                print(f"\n{provider}:")
                if isinstance(data, dict) and "error" in data:
                    print(f"  Error: {data['error']}")
                elif not data:
                    print("  No records found.")
                else:
                    for r in data:
                        print(f"  {r}")

        sys.exit(0)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
