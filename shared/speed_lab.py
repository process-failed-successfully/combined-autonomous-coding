import os
import time
import socket
import sys
import requests
import threading
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

class SpeedLabManager:
    """
    Manages system performance benchmarks: Internet, Disk, and Local Network.
    """

    def __init__(self):
        pass

    def check_internet_speed(self, url: str = "http://speedtest.tele2.net/10MB.zip", timeout: int = 30) -> Dict[str, Any]:
        """
        Measures internet download speed using a test file.
        Default URL is a common speedtest file (Tele2).
        """
        print(f"Testing download speed from {url}...")
        try:
            start_time = time.time()
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            total_bytes = 0
            # Chunk size 8KB
            for chunk in response.iter_content(chunk_size=8192):
                total_bytes += len(chunk)

            end_time = time.time()
            duration = end_time - start_time

            if duration == 0:
                duration = 0.001 # Prevent div by zero

            speed_bps = (total_bytes * 8) / duration
            speed_mbps = speed_bps / (1024 * 1024)

            return {
                "success": True,
                "url": url,
                "size_bytes": total_bytes,
                "duration_seconds": duration,
                "speed_mbps": speed_mbps
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_disk_speed(self, size_mb: int = 100, path: str = ".") -> Dict[str, Any]:
        """
        Measures disk write and read speed.
        """
        file_path = Path(path) / "speed_lab_test.tmp"
        size_bytes = size_mb * 1024 * 1024
        buffer_size = 1024 * 1024 # 1MB buffer
        data = os.urandom(buffer_size)

        print(f"Testing Disk I/O ({size_mb} MB) at {file_path.absolute()}...")

        try:
            # --- Write Test ---
            start_write = time.time()
            with open(file_path, "wb") as f:
                for _ in range(size_mb):
                    f.write(data)
                f.flush()
                os.fsync(f.fileno()) # Force write to disk
            end_write = time.time()

            write_duration = end_write - start_write
            write_speed_mbps = size_mb / write_duration if write_duration > 0 else 0

            # --- Read Test ---
            # Clear OS cache? Hard to do portably.
            # We assume reading back a newly written file might be cached,
            # but for a simple lab tool, it gives an upper bound.

            start_read = time.time()
            with open(file_path, "rb") as f:
                while f.read(buffer_size):
                    pass
            end_read = time.time()

            read_duration = end_read - start_read
            read_speed_mbps = size_mb / read_duration if read_duration > 0 else 0

            return {
                "success": True,
                "file": str(file_path),
                "write_speed_mbps": write_speed_mbps,
                "read_speed_mbps": read_speed_mbps,
                "write_duration": write_duration,
                "read_duration": read_duration
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    pass

    def run_network_server(self, host: str = "0.0.0.0", port: int = 5201):
        """
        Starts a simple TCP server to sink data and measure throughput.
        """
        print(f"Starting Speed Lab Server on {host}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))  # nosec B104
            s.listen()

            while True:
                conn, addr = s.accept()
                print(f"Connection from {addr}")
                self._handle_client(conn)

    def _handle_client(self, conn):
        with conn:
            total_bytes = 0
            start_time = time.time()
            try:
                while True:
                    data = conn.recv(65536) # 64KB buffer
                    if not data:
                        break
                    total_bytes += len(data)
            except Exception as e:
                print(f"Error reading from client: {e}")

            end_time = time.time()
            duration = end_time - start_time
            if duration == 0: duration = 0.001

            speed_mbps = (total_bytes * 8) / (duration * 1024 * 1024)
            print(f"Received {total_bytes / (1024*1024):.2f} MB in {duration:.2f}s. Speed: {speed_mbps:.2f} Mbps")

    def run_network_client(self, host: str, port: int = 5201, duration: int = 10):
        """
        Connects to server and pushes data to measure upload speed.
        """
        print(f"Connecting to {host}:{port} for {duration}s test...")
        data = os.urandom(65536) # 64KB random payload
        total_bytes = 0

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))

                start_time = time.time()
                end_time = start_time + duration

                while time.time() < end_time:
                    s.sendall(data)
                    total_bytes += len(data)

                real_duration = time.time() - start_time
                speed_mbps = (total_bytes * 8) / (real_duration * 1024 * 1024)

                print(f"--- Result ---")
                print(f"Sent:     {total_bytes / (1024*1024):.2f} MB")
                print(f"Duration: {real_duration:.2f} s")
                print(f"Speed:    {speed_mbps:.2f} Mbps")

        except ConnectionRefusedError:
            print(f"❌ Connection refused. Is the server running on {host}:{port}?")
        except Exception as e:
            print(f"❌ Error: {e}")


def run_speed_lab_logic(args):
    """CLI logic for Speed Lab."""
    manager = SpeedLabManager()

    if args.action == "internet":
        result = manager.check_internet_speed(timeout=args.timeout)
        if result["success"]:
            print(f"✅ Internet Download Speed: {result['speed_mbps']:.2f} Mbps")
            print(f"   Downloaded {result['size_bytes'] / (1024*1024):.2f} MB in {result['duration_seconds']:.2f}s")
        else:
            print(f"❌ Internet Speed Test Failed: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "disk":
        result = manager.check_disk_speed(size_mb=args.size)
        if result["success"]:
            print(f"✅ Disk Write Speed: {result['write_speed_mbps']:.2f} MB/s")
            print(f"✅ Disk Read Speed:  {result['read_speed_mbps']:.2f} MB/s")
        else:
            print(f"❌ Disk Speed Test Failed: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "local":
        if args.server:
            # Default host for server if not specified
            host = args.host or "0.0.0.0"  # nosec B104
            try:
                manager.run_network_server(host=host, port=args.port)
            except KeyboardInterrupt:
                print("\nServer stopped.")
        else:
            # Client requires host
            if not args.host:
                print("Error: --host required for client mode (or use --server).", file=sys.stderr)
                sys.exit(1)
            manager.run_network_client(host=args.host, port=args.port, duration=args.duration)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
