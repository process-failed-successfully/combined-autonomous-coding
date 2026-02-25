import psutil
import datetime
from typing import List, Dict, Any, Optional

class ProcessExplorerManager:
    """Manages system processes using psutil."""

    def list_processes(self, sort_by: str = "cpu", filter_text: str = "") -> List[Dict[str, Any]]:
        """
        Lists all running processes.
        Args:
            sort_by: Field to sort by ('cpu', 'memory', 'pid', 'name').
            filter_text: Text to filter by name or user.
        """
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'create_time', 'cmdline']):
            try:
                info = p.info
                # Handle potentially None values
                name = info['name'] or ""
                user = info['username'] or ""
                cmdline = " ".join(info['cmdline'] or [])

                # Filter
                if filter_text:
                    ft = filter_text.lower()
                    if ft not in name.lower() and ft not in user.lower() and ft not in str(info['pid']):
                        continue

                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Sort
        if sort_by == "cpu":
            procs.sort(key=lambda x: x.get('cpu_percent', 0.0), reverse=True)
        elif sort_by == "memory":
            procs.sort(key=lambda x: x.get('memory_percent', 0.0), reverse=True)
        elif sort_by == "pid":
            procs.sort(key=lambda x: x.get('pid', 0))
        elif sort_by == "name":
            procs.sort(key=lambda x: x.get('name', "").lower())

        return procs

    def get_process_details(self, pid: int) -> Dict[str, Any]:
        """Gets detailed info for a process."""
        try:
            p = psutil.Process(pid)
            details = p.as_dict(attrs=[
                'pid', 'name', 'username', 'status', 'create_time',
                'cpu_percent', 'memory_percent', 'cmdline', 'cwd', 'exe',
                'nice', 'ionice', 'num_threads'
            ])

            # Environment variables (might fail permission)
            try:
                details['environ'] = p.environ()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                details['environ'] = {}

            # Open files (might fail permission)
            try:
                details['open_files'] = [f.path for f in p.open_files()]
            except (psutil.AccessDenied, psutil.ZombieProcess):
                details['open_files'] = []

            # Connections (might fail permission)
            try:
                conns = []
                for c in p.connections():
                    laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "?"
                    raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "?"
                    conns.append(f"{c.type} {laddr} -> {raddr} ({c.status})")
                details['connections'] = conns
            except (psutil.AccessDenied, psutil.ZombieProcess):
                details['connections'] = []

            return details
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            return {"error": str(e)}

    def kill_process(self, pid: int, force: bool = False) -> bool:
        """Kills a process."""
        try:
            p = psutil.Process(pid)
            if force:
                p.kill() # SIGKILL
            else:
                p.terminate() # SIGTERM
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def suspend_process(self, pid: int) -> bool:
        """Suspends a process (SIGSTOP)."""
        try:
            p = psutil.Process(pid)
            p.suspend()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def resume_process(self, pid: int) -> bool:
        """Resumes a process (SIGCONT)."""
        try:
            p = psutil.Process(pid)
            p.resume()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
