import socket
import requests
import subprocess
import platform
import sys
import json
from typing import List, Dict, Any


class NetLabManager:
    """
    Manages network diagnostics and utilities.
    """

    def scan_ports(self, host: str, ports: List[int]) -> Dict[int, str]:
        """
        Scans specific ports on a host to check if they are open.
        """
        results = {}
        for port in ports:
            try:
                # Use a short timeout for scanning
                with socket.create_connection((host, port), timeout=0.5):
                    results[port] = "Open"
            except (socket.timeout, ConnectionRefusedError):
                results[port] = "Closed"
            except Exception as e:
                results[port] = f"Error: {e}"
        return results

    def dns_lookup(self, domain: str, record_type: str = "A") -> Dict[str, Any]:
        """
        Performs a DNS lookup.
        Currently supports A records via socket.
        """
        results: Dict[str, Any] = {}
        try:
            if record_type.upper() == "A":
                # Returns (hostname, aliaslist, ipaddrlist)
                _, aliases, ips = socket.gethostbyname_ex(domain)
                results['A'] = ips
                if aliases:
                    results['Aliases'] = aliases
            else:
                # Basic socket only supports A (and AAAA via getaddrinfo) easily without dnspython
                # We'll try getaddrinfo for others or fail gracefully
                if record_type.upper() == "AAAA":
                    info = socket.getaddrinfo(domain, None, socket.AF_INET6)
                    # Extract IP address from sockaddr tuple (address, port, flow info, scope id)
                    # We cast to str just to be safe for mypy
                    extracted_ips: List[str] = [str(x[4][0]) for x in info]
                    results['AAAA'] = list(set(extracted_ips))
                else:
                    return {"error": f"Record type {record_type} not supported without external libraries."}

        except socket.gaierror as e:
            results['error'] = str(e)
        except Exception as e:
            results['error'] = str(e)
        return results

    def http_head(self, url: str) -> Dict[str, Any]:
        """
        Fetches HTTP headers for a URL.
        """
        try:
            if not url.startswith("http"):
                url = "http://" + url
            response = requests.head(url, timeout=5)
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
        except Exception as e:
            return {"error": str(e)}

    def ping(self, host: str, count: int = 4) -> bool:
        """
        Pings a host using the system ping command.
        """
        # Platform agnostic ping
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, str(count), host]

        # Suppress output? Users might want to see it.
        # But if we return bool, we usually suppress.
        # Let's let it print to stdout since it's a CLI tool,
        # but also return success status.
        try:
            return subprocess.call(command) == 0
        except Exception:
            return False

    def traceroute(self, host: str, max_hops: int = 30) -> Dict[str, Any]:
        """
        Traceroutes a host using the system command.
        """
        cmd = 'tracert' if platform.system().lower() == 'windows' else 'traceroute'

        # Determine the flag for max hops based on the command
        if cmd == 'tracert':
            command = [cmd, '-h', str(max_hops), host]
        else:
            command = [cmd, '-m', str(max_hops), host]

        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr or result.stdout or "Command failed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Traceroute timed out."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_ip_info(self) -> Dict[str, str]:
        """
        Gets local and public IP addresses.
        """
        info = {}

        # Local IP
        try:
            # Connect to an external server to determine the interface used
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Doesn't actually connect
                s.connect(("8.8.8.8", 80))
                info["local_ip"] = s.getsockname()[0]
        except Exception:
            info["local_ip"] = "Unavailable"

        # Public IP
        try:
            info["public_ip"] = requests.get("https://api.ipify.org", timeout=5).text
        except Exception:
            info["public_ip"] = "Unavailable"

        return info


def run_net_lab_logic(args):
    """
    CLI entry point for Net Lab.
    """
    if getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Net Lab TUI...")
        app = AgentTUI(project_dir=args.project_dir, start_tab="tab-net-diag")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
        sys.exit(0)

    manager = NetLabManager()

    if args.action == "scan":
        host = args.host

        # Parse ports
        ports: List[int] = []
        if args.ports:
            parts = args.ports.split(',')
            for part in parts:
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    ports.extend(range(start, end + 1))
                else:
                    ports.append(int(part))
        else:
            # Default scan range
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 3000, 3306, 5432, 8000, 8080]

        print(f"--- Port Scan: {host} ---")
        scan_results = manager.scan_ports(host, ports)

        print(f"{'Port':<8} | {'Status'}")
        print("-" * 20)
        for port in sorted(scan_results.keys()):
            status = scan_results[port]
            # Colorize
            if status == "Open":
                status = f"\033[92m{status}\033[0m"
            elif status == "Closed":
                status = f"\033[91m{status}\033[0m"
            print(f"{port:<8} | {status}")
        sys.exit(0)

    elif args.action == "dns":
        domain = args.domain
        rtype = args.type

        print(f"--- DNS Lookup ({rtype}): {domain} ---")
        dns_results = manager.dns_lookup(domain, rtype)

        if "error" in dns_results:
            print(f"❌ Error: {dns_results['error']}", file=sys.stderr)
            sys.exit(1)

        print(json.dumps(dns_results, indent=2))
        sys.exit(0)

    elif args.action == "head":
        url = args.url
        print(f"--- HTTP HEAD: {url} ---")
        head_result = manager.http_head(url)

        if "error" in head_result:
            print(f"❌ Error: {head_result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"Status Code: {head_result['status_code']}")
        print("Headers:")
        for k, v in head_result['headers'].items():
            print(f"  {k}: {v}")
        sys.exit(0)

    elif args.action == "ping":
        host = args.host
        count = args.count
        print(f"--- Pinging {host} ({count} times) ---")
        success = manager.ping(host, count)
        if success:
            print("\n✅ Ping successful.")
            sys.exit(0)
        else:
            print("\n❌ Ping failed.")
            sys.exit(1)

    elif args.action == "traceroute":
        host = args.host
        max_hops = args.max_hops
        print(f"--- Traceroute to {host} (max {max_hops} hops) ---")
        result = manager.traceroute(host, max_hops)
        if result.get("success"):
            print(result.get("output", ""))
            sys.exit(0)
        else:
            print(f"❌ Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "ip":
        print("--- IP Information ---")
        info = manager.get_ip_info()
        print(f"Local IP:  {info['local_ip']}")
        print(f"Public IP: {info['public_ip']}")
        sys.exit(0)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
