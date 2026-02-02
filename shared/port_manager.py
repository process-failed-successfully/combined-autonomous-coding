import psutil
import sys
import time
import argparse
from typing import List, Dict, Any, Optional

class PortManager:
    """
    Manages network ports and processes.
    """

    @staticmethod
    def list_listening_ports() -> List[Dict[str, Any]]:
        """
        Lists all listening ports and their associated processes.
        """
        results = []
        try:
            # Check TCP and UDP listening ports
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.status == 'LISTEN':
                    pid = conn.pid
                    name = ""
                    try:
                        proc = psutil.Process(pid)
                        name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                    results.append({
                        'port': conn.laddr.port,
                        'pid': pid,
                        'name': name,
                        'type': 'TCP' if conn.type == 1 else 'UDP' # 1=TCP, 2=UDP
                    })
        except (psutil.AccessDenied, psutil.Error) as e:
            print(f"Error listing ports: {e}", file=sys.stderr)

        # Sort by port number
        results.sort(key=lambda x: x['port'])
        return results

    @staticmethod
    def check_port(port: int) -> Optional[Dict[str, Any]]:
        """
        Checks if a specific port is in use. Returns details if used, None otherwise.
        """
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    pid = conn.pid
                    name = ""
                    try:
                        proc = psutil.Process(pid)
                        name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                    return {
                        'port': port,
                        'pid': pid,
                        'name': name,
                        'active': True
                    }
        except Exception as e:
            print(f"Error checking port {port}: {e}", file=sys.stderr)

        return None

    @staticmethod
    def kill_port(port: int, force: bool = False) -> bool:
        """
        Kills the process listening on the specified port.
        """
        info = PortManager.check_port(port)
        if not info:
            print(f"Port {port} is not in use.")
            return False

        pid = info['pid']
        try:
            proc = psutil.Process(pid)
            print(f"Killing process {pid} ({info['name']}) on port {port}...")
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                if force:
                    print("Process did not terminate, forcing kill...")
                    proc.kill()
                    proc.wait(timeout=3)
                else:
                    print("Process did not terminate. Use --force to kill.")
                    return False

            print(f"✅ Process {pid} killed.")
            return True

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error) as e:
            print(f"Error killing process {pid}: {e}", file=sys.stderr)
            return False

    @staticmethod
    def wait_for_port(port: int, state: str = 'free', timeout: int = 30) -> bool:
        """
        Waits for a port to become 'free' or 'active'.
        """
        start_time = time.time()
        print(f"Waiting for port {port} to be {state} (timeout: {timeout}s)...")

        while time.time() - start_time < timeout:
            info = PortManager.check_port(port)
            is_active = info is not None

            if state == 'free' and not is_active:
                print(f"✅ Port {port} is now free.")
                return True
            elif state == 'active' and is_active:
                print(f"✅ Port {port} is now active (PID: {info['pid']}).")
                return True

            time.sleep(0.5)

        print(f"❌ Timeout waiting for port {port} to be {state}.")
        return False

def run_port_manager_cli(args):
    """
    CLI entry point for Port Manager.
    """
    manager = PortManager()

    if args.action == "list":
        ports = manager.list_listening_ports()
        if not ports:
            print("No listening ports found (or permission denied).")
        else:
            print(f"{'PORT':<8} | {'PID':<8} | {'TYPE':<5} | {'PROCESS NAME'}")
            print("-" * 50)
            for p in ports:
                pid_str = str(p['pid']) if p['pid'] else "N/A"
                print(f"{p['port']:<8} | {pid_str:<8} | {p['type']:<5} | {p['name']}")

    elif args.action == "check":
        if not args.port:
            print("Error: --port required for check.")
            sys.exit(1)

        info = manager.check_port(args.port)
        if info:
            print(f"Port {args.port} is ACTIVE.")
            print(f"Process: {info['name']} (PID: {info['pid']})")
        else:
            print(f"Port {args.port} is FREE.")

    elif args.action == "kill":
        if not args.port:
            print("Error: --port required for kill.")
            sys.exit(1)

        success = manager.kill_port(args.port, force=args.force)
        sys.exit(0 if success else 1)

    elif args.action == "wait":
        if not args.port:
            print("Error: --port required for wait.")
            sys.exit(1)

        success = manager.wait_for_port(args.port, state=args.state, timeout=args.timeout)
        sys.exit(0 if success else 1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
