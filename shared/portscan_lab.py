import asyncio
import socket
from typing import List, Dict, Tuple, Optional
import sys

# Common ports dictionary
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    465: "SMTPS",
    587: "SMTP (Submission)",
    993: "IMAPS",
    995: "POP3S",
    3306: "MySQL",
    5432: "PostgreSQL",
    6379: "Redis",
    8080: "HTTP-Alt",
    27017: "MongoDB",
}

class PortScanManager:
    """Manager for asynchronous port scanning."""

    def __init__(self):
        self._cancel_flag = False

    def cancel(self):
        self._cancel_flag = True

    async def check_port(self, host: str, port: int, timeout: float = 1.0) -> Tuple[int, bool, str]:
        """Check if a specific port is open."""
        if self._cancel_flag:
            return port, False, ""

        try:
            # Create a socket and set a timeout
            conn = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(conn, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            service = COMMON_PORTS.get(port, "Unknown")
            return port, True, service
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return port, False, ""

    async def scan_ports(self, host: str, start_port: int, end_port: int,
                         timeout: float = 1.0, concurrency: int = 100,
                         callback=None) -> List[Dict[str, str]]:
        """Scans a range of ports concurrently."""
        self._cancel_flag = False
        open_ports = []

        # Determine actual port range
        ports_to_scan = list(range(start_port, end_port + 1))

        semaphore = asyncio.Semaphore(concurrency)

        async def scan_with_sem(port: int):
            async with semaphore:
                result = await self.check_port(host, port, timeout)
                if callback:
                    callback(result)
                return result

        # Create tasks
        tasks = [asyncio.create_task(scan_with_sem(port)) for port in ports_to_scan]

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)

        for port, is_open, service in results:
            if is_open:
                open_ports.append({
                    "port": str(port),
                    "service": service
                })

        # Sort by port number
        open_ports.sort(key=lambda x: int(x["port"]))
        return open_ports

def parse_port_range(port_str: str) -> Tuple[int, int]:
    """Parse a port range string (e.g., '80', '1-1000')."""
    if "-" in port_str:
        parts = port_str.split("-")
        if len(parts) == 2:
            try:
                start = int(parts[0])
                end = int(parts[1])
                return start, end
            except ValueError:
                pass
    else:
        try:
            port = int(port_str)
            return port, port
        except ValueError:
            pass
    raise ValueError(f"Invalid port format: {port_str}. Use '80' or '1-1000'.")

async def run_portscan_cli_logic(args):
    """Runs the CLI logic for PortScan Lab."""
    manager = PortScanManager()

    try:
        start_port, end_port = parse_port_range(args.ports)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    print(f"Scanning {args.host} for ports {start_port}-{end_port} (Timeout: {args.timeout}s)...")

    open_ports = await manager.scan_ports(
        host=args.host,
        start_port=start_port,
        end_port=end_port,
        timeout=args.timeout,
        concurrency=args.concurrency
    )

    if not open_ports:
        print(f"No open ports found on {args.host} in range {start_port}-{end_port}.")
    else:
        print("\nOpen Ports:")
        print("-" * 30)
        print(f"{'Port':<10} | {'Service':<15}")
        print("-" * 30)
        for item in open_ports:
            print(f"{item['port']:<10} | {item['service']:<15}")

    return True
