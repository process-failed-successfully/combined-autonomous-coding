import asyncio
import sys
import os
import signal
from pathlib import Path
from typing import Dict, List, Optional, Callable
import platform

class ProcLabManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.processes: Dict[str, asyncio.subprocess.Process] = {}
        self.process_defs: Dict[str, str] = {}
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

    def load_config(self, procfile_path: Path) -> None:
        self.process_defs = self.parse_procfile(procfile_path)

    async def _stream_output(self, name: str, stream, on_output: Optional[Callable[[str, str], None]] = None, color_code: str = "37"):
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded = line.decode().strip()
            if decoded:
                if on_output:
                    # Callback gets (process_name, line)
                    if asyncio.iscoroutinefunction(on_output):
                        await on_output(name, decoded)
                    else:
                        on_output(name, decoded)
                else:
                    # Default CLI output
                    print(f"\033[{color_code}m[{name}]\033[0m {decoded}")

    async def start_process(self, name: str, on_output: Optional[Callable[[str, str], None]] = None):
        if name not in self.process_defs:
            raise ValueError(f"Process '{name}' not found in definitions.")

        if name in self.processes and self.processes[name].returncode is None:
            # Already running
            return

        command = self.process_defs[name]

        # Prepare subprocess arguments
        kwargs = {
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "cwd": self.project_dir,
        }

        # Use setsid on Unix to easily kill process groups
        if sys.platform != "win32":
            kwargs["preexec_fn"] = os.setsid

        # Create subprocess
        process = await asyncio.create_subprocess_shell(
            command,
            **kwargs
        )

        self.processes[name] = process

        # Assign a simple color based on name hash or something simpler for consistency
        # For now, just use a default or cycle if we had an index.
        # Since this method starts one, we pick a color.
        colors = ["32", "33", "34", "35", "36", "31"]
        color = colors[hash(name) % len(colors)]

        # Create tasks for streaming stdout and stderr
        # We store these tasks to ensure they run?
        # Actually, we should probably fire and forget or track them if we want to wait.
        # For TUI, fire and forget (or track in background) is better.

        t1 = asyncio.create_task(self._stream_output(name, process.stdout, on_output, color))
        t2 = asyncio.create_task(self._stream_output(name, process.stderr, on_output, color))
        self.tasks.extend([t1, t2])

    async def stop_process(self, name: str):
        if name in self.processes:
            p = self.processes[name]
            if p.returncode is None:
                try:
                    if sys.platform != "win32":
                        try:
                            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                    else:
                        p.terminate()

                    try:
                        await asyncio.wait_for(p.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        if sys.platform != "win32":
                             try:
                                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                             except ProcessLookupError:
                                pass
                        else:
                            p.kill()
                        await p.wait()

                except ProcessLookupError:
                    pass
            del self.processes[name]

    async def stop_all(self):
        # Create list of stop tasks to run concurrently
        stop_tasks = [self.stop_process(name) for name in list(self.processes.keys())]
        if stop_tasks:
            await asyncio.gather(*stop_tasks)

    # CLI Compatibility Method
    async def start_processes(self, procfile_path: Path, specific_process: Optional[str] = None):
        self.load_config(procfile_path)

        targets = [specific_process] if specific_process else list(self.process_defs.keys())

        if not targets:
            print("No processes to start.")
            return

        print(f"Starting {len(targets)} process(es)...")
        print("Press Ctrl+C to stop.")

        try:
            for name in targets:
                await self.start_process(name)

            # Wait for all processes to exit or cancellation
            # We can wait on the process objects
            while True:
                running = [p for p in self.processes.values() if p.returncode is None]
                if not running:
                    break
                await asyncio.sleep(0.1)

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
    filename = getattr(args, 'file', None) or "Procfile"
    procfile_path = args.project_dir / filename

    if args.action == "start":
        try:
            await manager.start_processes(procfile_path)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
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
            pass
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
