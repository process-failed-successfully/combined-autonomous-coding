import psutil
import os
import signal
from typing import List, Dict, Any, Optional

class ProcessExplorerManager:
    """Manages system processes for the Process Explorer."""

    def __init__(self):
        pass

    def list_processes(self, filter_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists all running processes.

        Args:
            filter_str: Optional string to filter by name or PID.

        Returns:
            List of process dictionaries.
        """
        processes = []
        try:
            # Iterate over all running processes
            for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent', 'cmdline', 'create_time']):
                try:
                    info = proc.info

                    # Basic filtering
                    if filter_str:
                        filter_lower = filter_str.lower()
                        name_match = filter_lower in info['name'].lower()
                        pid_match = filter_lower in str(info['pid'])
                        if not (name_match or pid_match):
                            continue

                    # Format CPU/Mem
                    # cpu_percent can be 0.0 on first call, but psutil usually handles it if called repeatedly?
                    # Actually for interval=None it returns since last call.
                    # TUI calling this repeatedly will work fine.

                    processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            # Fallback or empty if critical failure
            print(f"Error listing processes: {e}")

        return processes

    def get_process_details(self, pid: int) -> Dict[str, Any]:
        """
        Gets detailed information about a process.
        """
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                return {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "status": proc.status(),
                    "username": proc.username(),
                    "create_time": proc.create_time(),
                    "cpu_percent": proc.cpu_percent(),
                    "memory_info": proc.memory_info()._asdict(),
                    "cmdline": proc.cmdline(),
                    "cwd": proc.cwd(),
                    "exe": proc.exe(),
                    "nice": proc.nice(),
                    "threads": proc.num_threads(),
                    "open_files": [f.path for f in proc.open_files()] if hasattr(proc, 'open_files') else [],
                    "connections": [c._asdict() for c in proc.connections()] if hasattr(proc, 'connections') else [],
                    "environ": proc.environ()
                }
        except psutil.NoSuchProcess:
            return {"error": f"Process {pid} not found."}
        except psutil.AccessDenied:
            return {"error": f"Access denied to process {pid}."}
        except Exception as e:
            return {"error": f"Error retrieving details: {e}"}

    def kill_process(self, pid: int, force: bool = False) -> bool:
        """Kills a process."""
        try:
            proc = psutil.Process(pid)
            if force:
                proc.kill()
            else:
                proc.terminate()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def suspend_process(self, pid: int) -> bool:
        """Suspends a process."""
        try:
            proc = psutil.Process(pid)
            proc.suspend()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def resume_process(self, pid: int) -> bool:
        """Resumes a process."""
        try:
            proc = psutil.Process(pid)
            proc.resume()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
