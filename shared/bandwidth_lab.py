try:
    import psutil
except ImportError:
    psutil = None

import time
import sys
import argparse
from typing import Dict, Any, Generator, Optional, List

class BandwidthManager:
    """
    Manages network bandwidth monitoring.
    """

    def __init__(self):
        if psutil is None:
            self.error = "psutil library not found. Please install it."
        else:
            self.error = None

    def get_io_counters(self) -> Dict[str, Any]:
        """
        Returns network I/O statistics per interface.
        """
        if self.error:
            return {"error": self.error}

        try:
            return psutil.net_io_counters(pernic=True)
        except Exception as e:
            return {"error": str(e)}

    def get_interfaces(self) -> List[str]:
        """
        Returns a list of available network interfaces.
        """
        counters = self.get_io_counters()
        if "error" in counters:
            return []
        return list(counters.keys())

    def monitor(self, interfaces: Optional[List[str]] = None, interval: float = 1.0) -> Generator[Dict[str, Any], None, None]:
        """
        Generator that yields bandwidth usage stats (speed) per interval.
        """
        if self.error:
            yield {"error": self.error}
            return

        # Initial sample
        prev_counters = self.get_io_counters()
        if "error" in prev_counters:
            yield {"error": prev_counters["error"]}
            return

        while True:
            time.sleep(interval)
            curr_counters = self.get_io_counters()
            if "error" in curr_counters:
                yield {"error": curr_counters["error"]}
                break

            stats = {}
            timestamp = time.time()

            # Identify all interfaces (union of keys)
            all_ifaces = set(prev_counters.keys()) | set(curr_counters.keys())

            for iface in all_ifaces:
                # Filter if needed
                if interfaces and iface not in interfaces:
                    continue

                prev = prev_counters.get(iface)
                curr = curr_counters.get(iface)

                if prev and curr:
                    # Bytes sent/recv diff
                    bytes_sent_diff = curr.bytes_sent - prev.bytes_sent
                    bytes_recv_diff = curr.bytes_recv - prev.bytes_recv

                    # Packets sent/recv diff
                    packets_sent_diff = curr.packets_sent - prev.packets_sent
                    packets_recv_diff = curr.packets_recv - prev.packets_recv

                    # Speed (bytes/sec) - assuming interval is accurate enough, or calculate exact delta
                    # For simple monitoring, we assume sleep(interval) is close enough

                    stats[iface] = {
                        "bytes_sent_sec": bytes_sent_diff / interval,
                        "bytes_recv_sec": bytes_recv_diff / interval,
                        "packets_sent_sec": packets_sent_diff / interval,
                        "packets_recv_sec": packets_recv_diff / interval,
                        "total_bytes_sent": curr.bytes_sent,
                        "total_bytes_recv": curr.bytes_recv,
                        "total_packets_sent": curr.packets_sent,
                        "total_packets_recv": curr.packets_recv
                    }

            yield {"timestamp": timestamp, "interfaces": stats}
            prev_counters = curr_counters

def _bytes_to_human(n: float, per_second: bool = True) -> str:
    """Helper to format bytes."""
    symbols = ('K', 'M', 'G', 'T', 'P')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10

    unit = "B"
    value = n

    for s in reversed(symbols):
        if n >= prefix[s]:
            value = n / prefix[s]
            unit = s + "B"
            break

    suffix = "/s" if per_second else ""
    return f"{value:.2f} {unit}{suffix}"

def run_bandwidth_lab_logic(args: argparse.Namespace) -> None:
    """CLI Entry point for Bandwidth Lab."""
    manager = BandwidthManager()

    if args.action == "list":
        print("--- Network Interfaces & Totals ---")
        counters = manager.get_io_counters()
        if "error" in counters:
            print(f"Error: {counters['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"{'Interface':<15} | {'Sent (Total)':<15} | {'Recv (Total)':<15}")
        print("-" * 50)

        for iface, stats in counters.items():
            sent = _bytes_to_human(stats.bytes_sent, per_second=False)
            recv = _bytes_to_human(stats.bytes_recv, per_second=False)
            print(f"{iface:<15} | {sent:<15} | {recv:<15}")
        sys.exit(0)

    elif args.action == "monitor":
        interfaces = args.interface.split(",") if args.interface else None
        print(f"Monitoring bandwidth (Interval: {args.interval}s)... Press Ctrl+C to stop.")

        try:
            for sample in manager.monitor(interfaces=interfaces, interval=args.interval):
                if "error" in sample:
                    print(f"Error: {sample['error']}", file=sys.stderr)
                    break

                # Clear screen (ANSI)
                print("\033[H\033[J", end="")
                print(f"--- Bandwidth Monitor ({time.ctime(sample['timestamp'])}) ---")
                print(f"{'Interface':<15} | {'Upload Speed':<15} | {'Download Speed':<15}")
                print("-" * 50)

                for iface, stats in sample["interfaces"].items():
                    up = _bytes_to_human(stats["bytes_sent_sec"])
                    down = _bytes_to_human(stats["bytes_recv_sec"])
                    print(f"{iface:<15} | {up:<15} | {down:<15}")

        except KeyboardInterrupt:
            print("\nStopped.")
            sys.exit(0)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
