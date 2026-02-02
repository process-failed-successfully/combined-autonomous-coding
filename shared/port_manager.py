import psutil
import time
import sys
from typing import List, Dict, Optional, Any
from pathlib import Path

class PortManager:
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir

    def list_listening_ports(self) -> List[Dict[str, Any]]:
        """Returns a list of listening ports with process info."""
        results = []
        try:
            # Check for TCP listening ports
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.status == psutil.CONN_LISTEN:
                    pid = conn.pid
                    process_name = "Unknown"
                    try:
                        if pid:
                            process = psutil.Process(pid)
                            process_name = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                    results.append({
                        "port": conn.laddr.port,
                        "pid": pid,
                        "name": process_name,
                        "address": conn.laddr.ip
                    })
        except Exception as e:
            print(f"Error listing ports: {e}", file=sys.stderr)

        # Sort by port number
        return sorted(results, key=lambda x: x['port'])

    def check_port(self, port: int) -> Optional[Dict[str, Any]]:
        """Returns process info if port is in use, else None."""
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.laddr.port == port:
                    pid = conn.pid
                    process_name = "Unknown"
                    try:
                        if pid:
                            process = psutil.Process(pid)
                            process_name = process.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                    return {
                        "port": port,
                        "pid": pid,
                        "name": process_name,
                        "status": conn.status,
                        "address": conn.laddr.ip
                    }
        except Exception as e:
            print(f"Error checking port {port}: {e}", file=sys.stderr)
        return None

    def kill_process_on_port(self, port: int) -> bool:
        """Kills the process using the port."""
        info = self.check_port(port)
        if not info or not info.get('pid'):
            return False

        pid = info['pid']
        try:
            process = psutil.Process(pid)
            process.terminate()
            try:
                process.wait(timeout=3)
            except psutil.TimeoutExpired:
                process.kill()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def wait_for_port(self, port: int, state: str = "free", timeout: float = 30.0) -> bool:
        """
        Waits for port to reach state ('free' or 'used').
        Returns True if state reached, False on timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            info = self.check_port(port)
            is_used = info is not None and info.get('status') == psutil.CONN_LISTEN

            if state == "free" and not is_used:
                return True
            if state == "used" and is_used:
                return True

            time.sleep(0.5)
        return False

def run_port_logic(project_dir: Path, action: str, port: Optional[int] = None, **kwargs) -> bool:
    manager = PortManager(project_dir)

    if action == "list":
        ports = manager.list_listening_ports()
        if not ports:
            print("No active listening ports found (that we have access to).")
            return True

        print(f"{'PORT':<8} | {'PID':<8} | {'PROCESS':<20} | {'ADDRESS'}")
        print("-" * 60)
        for p in ports:
            print(f"{p['port']:<8} | {str(p['pid']):<8} | {p['name']:<20} | {p['address']}")
        return True

    elif action == "check":
        if port is None:
            print("Error: Port number required for 'check'.", file=sys.stderr)
            return False

        info = manager.check_port(port)
        if info:
            print(f"Port {port} is IN USE.")
            print(f"  PID:     {info['pid']}")
            print(f"  Process: {info['name']}")
            print(f"  Status:  {info['status']}")
            print(f"  Address: {info['address']}")
        else:
            print(f"Port {port} is FREE.")
        return True

    elif action == "kill":
        if port is None:
            print("Error: Port number required for 'kill'.", file=sys.stderr)
            return False

        info = manager.check_port(port)
        if not info:
            print(f"Port {port} is not in use.", file=sys.stderr)
            return False

        print(f"Killing process on port {port} (PID: {info['pid']}, Name: {info['name']})...")
        if manager.kill_process_on_port(port):
            print(f"✅ Successfully killed process on port {port}.")
            return True
        else:
            print(f"❌ Failed to kill process on port {port} (Access Denied or Process Gone).", file=sys.stderr)
            return False

    elif action == "wait":
        if port is None:
            print("Error: Port number required for 'wait'.", file=sys.stderr)
            return False

        state = kwargs.get('state', 'free')
        timeout = kwargs.get('timeout', 30.0)

        print(f"Waiting for port {port} to become {state} (timeout: {timeout}s)...")
        if manager.wait_for_port(port, state, float(timeout)):
            print(f"✅ Port {port} is now {state}.")
            return True
        else:
            print(f"❌ Timeout waiting for port {port} to become {state}.", file=sys.stderr)
            return False

    return False
