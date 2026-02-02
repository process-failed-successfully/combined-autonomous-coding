import time
import socket
import psutil
from typing import Optional, Dict, List, Any

class PortManager:
    """
    Manages network ports and associated processes.
    """

    @staticmethod
    def get_process_on_port(port: int) -> Optional[Dict[str, Any]]:
        """
        Identify the process using a specific port.
        Returns a dictionary with process info or None if port is free.
        """
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            return {
                                "pid": conn.pid,
                                "name": proc.name(),
                                "cmdline": " ".join(proc.cmdline()),
                                "status": proc.status(),
                                "username": proc.username()
                            }
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            # Process might have died or we can't access it
                            return {
                                "pid": conn.pid,
                                "name": "unknown",
                                "cmdline": "",
                                "status": "unknown",
                                "username": "unknown"
                            }
        except (psutil.AccessDenied, PermissionError):
            # Fallback logic could go here if needed, but usually requires sudo
            pass
        return None

    @staticmethod
    def list_listening_ports() -> List[Dict[str, Any]]:
        """
        List all ports currently in LISTEN state.
        """
        results = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == psutil.CONN_LISTEN:
                    info = {
                        "port": conn.laddr.port,
                        "pid": conn.pid,
                        "name": "unknown",
                        "username": "unknown"
                    }
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            info["name"] = proc.name()
                            info["username"] = proc.username()
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            pass
                    results.append(info)
        except (psutil.AccessDenied, PermissionError):
            pass

        # Sort by port number
        results.sort(key=lambda x: x["port"])
        return results

    @staticmethod
    def kill_process_on_port(port: int, force: bool = False) -> bool:
        """
        Kill the process listening on the specified port.
        """
        proc_info = PortManager.get_process_on_port(port)
        if not proc_info or not proc_info.get("pid"):
            return False

        try:
            pid = proc_info["pid"]
            proc = psutil.Process(pid)
            if force:
                proc.kill()
            else:
                proc.terminate()

            # Wait for it to die
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                if not force:
                    # Escalating to kill
                    proc.kill()
                    proc.wait(timeout=2)

            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    @staticmethod
    def wait_for_port(port: int, state: str = "open", timeout: int = 30, host: str = "127.0.0.1") -> bool:
        """
        Wait for a port to reach a specific state ('open' or 'closed').
        'open': Wait until something is listening.
        'closed': Wait until the port is free.
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            is_open = False
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            try:
                result = sock.connect_ex((host, port))
                if result == 0:
                    is_open = True
            except Exception:
                pass
            finally:
                sock.close()

            if state == "open" and is_open:
                return True
            if state == "closed" and not is_open:
                return True

            time.sleep(0.5)

        return False
