import asyncio
import sys
import os
import signal
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import platform

class ProcLabManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.processes: Dict[str, asyncio.subprocess.Process] = {}
        self.tasks: List[asyncio.Task] = []

    def parse_procfile(self, procfile_path: Path) -> Dict[str, str]:
        if not procfile_path.exists():
            raise FileNotFoundError(f"Procfile not found: {procfile_path}")

        processes = {}
        with open(procfile_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(':', 1)
                if len(parts) != 2:
                    continue

                name, command = parts
                processes[name.strip()] = command.strip()

        return processes

    async def _stream_output(self, name: str, stream: asyncio.StreamReader, callback: Optional[Callable[[str, str], None]] = None):
        """
        Streams output line by line.
        callback(name, line)
        """
        while True:
            try:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode().strip()
                if decoded:
                    if callback:
                        callback(name, decoded)
                    else:
                        print(f"[{name}] {decoded}")
            except ValueError:
                continue

    async def start_process(self, name: str, command: str, log_callback: Optional[Callable[[str, str], None]] = None) -> bool:
        """Starts a single process."""
        if name in self.processes and self.processes[name].returncode is None:
            # Already running
            return False

        # Prepare subprocess arguments
        kwargs = {
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "cwd": self.project_dir,
        }

        # Use setsid on Unix to easily kill process groups
        if sys.platform != "win32":
            kwargs["preexec_fn"] = os.setsid

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                **kwargs
            )
            self.processes[name] = process

            # Create tasks for streaming stdout and stderr
            if process.stdout:
                task_out = asyncio.create_task(self._stream_output(name, process.stdout, log_callback))
                self.tasks.append(task_out)
            if process.stderr:
                task_err = asyncio.create_task(self._stream_output(name, process.stderr, log_callback))
                self.tasks.append(task_err)

            return True
        except Exception as e:
            if log_callback:
                log_callback(name, f"Error starting process: {e}")
            else:
                print(f"[{name}] Error starting process: {e}")
            return False

    async def stop_process(self, name: str) -> bool:
        """Stops a single process."""
        if name not in self.processes:
            return False

        proc = self.processes[name]
        if proc.returncode is not None:
            del self.processes[name]
            return True

        try:
            if sys.platform != "win32":
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()

            # Wait for it to actually stop with a timeout
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()

            del self.processes[name]
            return True
        except ProcessLookupError:
            del self.processes[name]
            return True
        except Exception:
            return False

    async def stop_all(self):
        """Stops all running processes."""
        names = list(self.processes.keys())
        for name in names:
            await self.stop_process(name)

        # Cancel streaming tasks
        for task in self.tasks:
            task.cancel()
        self.tasks = []

    async def start_processes(self, procfile_path: Path, specific_process: Optional[str] = None):
        """
        CLI compatibility method: starts processes and waits for them.
        """
        processes_map = self.parse_procfile(procfile_path)

        if specific_process:
            if specific_process not in processes_map:
                print(f"Process '{specific_process}' not found in Procfile.")
                return
            processes_map = {specific_process: processes_map[specific_process]}

        if not processes_map:
            print("No processes to start.")
            return

        # Assign colors for output prefixes (CLI only)
        colors = ["32", "33", "34", "35", "36", "31"] # Green, Yellow, Blue, Magenta, Cyan, Red

        def make_callback(color_code):
            def cb(p_name, line):
                print(f"\033[{color_code}m[{p_name}]\033[0m {line}")
            return cb

        print(f"Starting {len(processes_map)} process(es)...")
        print("Press Ctrl+C to stop.")

        try:
            start_tasks = []
            for i, (name, command) in enumerate(processes_map.items()):
                color = colors[i % len(colors)]
                start_tasks.append(self.start_process(name, command, make_callback(color)))

            await asyncio.gather(*start_tasks)

            # Wait for all processes to finish (or interruption)
            while self.processes:
                # Filter out finished processes
                active = [p for p in self.processes.values() if p.returncode is None]
                if not active:
                    break
                await asyncio.gather(*[p.wait() for p in active])

        except asyncio.CancelledError:
            print("\nStopping processes...")
            await self.stop_all()

    def list_processes(self, procfile_path: Path):
        try:
            processes = self.parse_procfile(procfile_path)
            print(f"--- Procfile: {procfile_path.name} ---")
            for name, cmd in processes.items():
                print(f"{name:<15} : {cmd}")
        except FileNotFoundError:
            print(f"Procfile not found at {procfile_path}")

async def run_proc_lab_logic(args):
    manager = ProcLabManager(args.project_dir)
    # Default to Procfile if not specified, but check for Procfile.dev etc?
    # args.file will be handled in main.py argument parsing or we assume default here.
    filename = getattr(args, 'file', None) or "Procfile"
    procfile_path = args.project_dir / filename

    if args.action == "start":
        try:
            await manager.start_processes(procfile_path)
        except (KeyboardInterrupt, asyncio.CancelledError):
            await manager.stop_all()
        except FileNotFoundError:
            print(f"Error: {filename} not found in {args.project_dir}")
            sys.exit(1)

    elif args.action == "run":
        if not getattr(args, 'process', None):
            print("Error: --process name required.")
            sys.exit(1)
        try:
            await manager.start_processes(procfile_path, specific_process=args.process)
        except (KeyboardInterrupt, asyncio.CancelledError):
            await manager.stop_all()
        except FileNotFoundError:
            print(f"Error: {filename} not found.")
            sys.exit(1)

    elif args.action == "list":
        manager.list_processes(procfile_path)

    elif args.action == "check":
        try:
            procs = manager.parse_procfile(procfile_path)
            print(f"✅ Valid Procfile with {len(procs)} process(es).")
        except Exception as e:
            print(f"❌ Invalid Procfile: {e}")
            sys.exit(1)
