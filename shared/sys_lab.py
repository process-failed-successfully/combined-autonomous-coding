import os
import sys
import psutil
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional


class SysLabManager:
    """
    Manages system information, processes, and disk usage.
    """

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def get_system_info(self) -> Dict[str, Any]:
        """
        Gathers comprehensive system information.
        """
        # System
        uname = platform.uname()
        system_info = {
            "os": f"{uname.system} {uname.release}",
            "version": uname.version,
            "machine": uname.machine,
            "processor": uname.processor,
            "python": platform.python_version()
        }

        # CPU
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "usage_percent": psutil.cpu_percent(interval=0.1),
        }
        try:
            freq = psutil.cpu_freq()
            if freq:
                cpu_info["freq_current"] = freq.current
                cpu_info["freq_min"] = freq.min
                cpu_info["freq_max"] = freq.max
        except FileNotFoundError:
            pass  # Freq not available on all systems

        # Memory
        mem = psutil.virtual_memory()
        mem_info = {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent
        }

        # Disk (Root)
        disk_usage = psutil.disk_usage("/")
        disk_info = {
            "root_total": disk_usage.total,
            "root_used": disk_usage.used,
            "root_free": disk_usage.free,
            "root_percent": disk_usage.percent
        }

        return {
            "system": system_info,
            "cpu": cpu_info,
            "memory": mem_info,
            "disk": disk_info
        }

    def list_processes(
        self,
        sort_by: str = "cpu",
        limit: int = 20,
        filter_name: Optional[str] = None,
        user: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lists processes based on criteria.
        """
        procs = []
        attrs = ['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'cmdline']

        for p in psutil.process_iter(attrs):
            try:
                p_info = p.info
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

            # Handle None values safely
            p_name = p_info.get('name') or ""
            p_user = p_info.get('username') or ""

            if filter_name and filter_name.lower() not in p_name.lower():
                continue

            if user and user != p_user:
                continue

            # Simplify cmdline
            cmd = " ".join(p_info['cmdline']) if p_info['cmdline'] else ""
            if len(cmd) > 50:
                cmd = cmd[:47] + "..."
            p_info['cmdline'] = cmd

            procs.append(p_info)

        # Sort
        reverse = True
        if sort_by == "cpu":
            def key(x): return x['cpu_percent'] or 0.0
        elif sort_by == "mem":
            def key(x): return x['memory_percent'] or 0.0
        elif sort_by == "pid":
            def key(x): return x['pid']
            reverse = False
        elif sort_by == "name":
            def key(x): return (x['name'] or "").lower()
            reverse = False
        else:
            def key(x): return x['cpu_percent'] or 0.0

        procs.sort(key=key, reverse=reverse)
        return procs[:limit]

    def kill_process(self, pid: Optional[int] = None, name: Optional[str] = None, signal_code: int = 15, force: bool = False) -> Dict[str, Any]:
        """
        Kills a process by PID or Name.
        """
        if pid:
            try:
                p = psutil.Process(pid)
                p.send_signal(signal_code)
                return {"success": True, "message": f"Sent signal {signal_code} to PID {pid} ({p.name()})"}
            except psutil.NoSuchProcess:
                return {"success": False, "message": f"PID {pid} not found."}
            except psutil.AccessDenied:
                return {"success": False, "message": f"Access denied to PID {pid}."}

        elif name:
            candidates = []
            for p in psutil.process_iter(['pid', 'name']):
                if p.info['name'] == name:
                    candidates.append(p)

            if not candidates:
                return {"success": False, "message": f"Process '{name}' not found."}

            if len(candidates) > 1 and not force:
                return {
                    "success": False,
                    "message": f"Found {len(candidates)} processes named '{name}'. Use --pid or --force to kill all.",
                    "pids": [p.pid for p in candidates]
                }

            killed = []
            failed = []
            for p in candidates:
                try:
                    p.send_signal(signal_code)
                    killed.append(p.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    failed.append(p.pid)

            msg = f"Sent signal {signal_code} to {len(killed)} processes."
            if failed:
                msg += f" Failed to kill {len(failed)} processes."
            return {"success": True, "message": msg, "killed": killed}

        return {"success": False, "message": "PID or Name required."}

    def analyze_disk_usage(self, path: Path, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Analyzes disk usage for a directory.
        Returns top N largest items.
        """
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist.")

        items = []
        try:
            with os.scandir(path) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            size = entry.stat().st_size
                            items.append({"path": entry.path, "name": entry.name, "size": size, "type": "file"})
                        elif entry.is_dir(follow_symlinks=False):
                            size = self._get_dir_size(entry.path)
                            items.append({"path": entry.path, "name": entry.name, "size": size, "type": "dir"})
                    except OSError:
                        continue
        except OSError as e:
            raise OSError(f"Error scanning directory: {e}")

        # Sort by size descending
        items.sort(key=lambda x: x["size"], reverse=True)
        return items[:limit]

    def _get_dir_size(self, path: str) -> int:
        """
        Calculates total size of a directory iteratively.
        """
        total = 0
        stack = [path]

        while stack:
            current_path = stack.pop()
            try:
                for entry in os.scandir(current_path):
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat().st_size
                    elif entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
            except OSError:
                pass
        return total

    def format_bytes(self, size: float) -> str:
        """
        Formats bytes to human readable string.
        """
        power = 1024
        n = 0
        power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
        while size >= power and n < 4:
            size /= power
            n += 1
        return f"{size:.2f} {power_labels[n]}"


def run_sys_lab_logic(args):
    """
    CLI logic for Sys Lab.
    """
    manager = SysLabManager(args.project_dir)

    if args.action == "info":
        info = manager.get_system_info()
        print("--- System Info ---")
        print(f"OS:       {info['system']['os']}")
        print(f"Kernel:   {info['system']['version']}")
        print(f"CPU:      {info['cpu']['physical_cores']} phys / {info['cpu']['logical_cores']} log ({info['cpu']['usage_percent']}%)")
        print(f"Memory:   {manager.format_bytes(info['memory']['used'])} / {manager.format_bytes(info['memory']['total'])} ({info['memory']['percent']}%)")
        print(
            f"Disk (/): {manager.format_bytes(info['disk']['root_used'])} / {manager.format_bytes(info['disk']['root_total'])} ({info['disk']['root_percent']}%)")
        sys.exit(0)

    elif args.action == "proc":
        procs = manager.list_processes(
            sort_by=args.sort,
            limit=args.limit,
            filter_name=args.filter,
            user=args.user
        )

        print(f"--- Processes (Top {len(procs)}) ---")
        # Header
        print(f"{'PID':<6} | {'User':<10} | {'CPU%':<5} | {'Mem%':<5} | {'Name':<20} | {'Command'}")
        print("-" * 80)

        for p in procs:
            pid = str(p['pid'])
            user = p['username'] or "?"
            cpu = f"{p['cpu_percent']:.1f}" if p['cpu_percent'] is not None else "?"
            mem = f"{p['memory_percent']:.1f}" if p['memory_percent'] is not None else "?"
            name = p['name'] or "?"
            cmd = p['cmdline'] or ""

            # Truncate
            if len(user) > 10:
                user = user[:9] + "."
            if len(name) > 20:
                name = name[:19] + "."

            print(f"{pid:<6} | {user:<10} | {cpu:<5} | {mem:<5} | {name:<20} | {cmd}")
        sys.exit(0)

    elif args.action == "kill":
        if not args.pid and not args.name:
            print("Error: --pid or --name required.", file=sys.stderr)
            sys.exit(1)

        result = manager.kill_process(
            pid=args.pid,
            name=args.name,
            signal_code=args.signal,
            force=args.force
        )

        if result["success"]:
            print(f"✅ {result['message']}")
            sys.exit(0)
        else:
            print(f"❌ {result['message']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "disk":
        # Resolve path argument (default to . if not provided)
        target_str = getattr(args, 'path', '.')
        target_path = Path(target_str).resolve()

        print(f"--- Disk Usage: {target_path} (Top {args.limit}) ---")
        print("Calculating sizes... (this may take a moment)")

        try:
            items = manager.analyze_disk_usage(target_path, limit=args.limit)

            if not items:
                print("Directory is empty.")
                sys.exit(0)

            print(f"{'Size':<10} | {'Type':<4} | {'Name'}")
            print("-" * 50)

            for item in items:
                size_str = manager.format_bytes(item['size'])
                itype = "DIR" if item['type'] == 'dir' else "FILE"
                print(f"{size_str:<10} | {itype:<4} | {item['name']}")

        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
