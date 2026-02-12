import asyncio
import sys
import os
import signal
from pathlib import Path
from typing import Dict, List, Optional
import platform

class ProcLabManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.processes = {}

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

    async def _stream_output(self, name: str, stream, color_code: str):
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded = line.decode().strip()
            if decoded:
                # Use simple ANSI colors for prefixes
                print(f"\033[{color_code}m[{name}]\033[0m {decoded}")

    async def start_processes(self, procfile_path: Path, specific_process: Optional[str] = None):
        processes_map = self.parse_procfile(procfile_path)

        if specific_process:
            if specific_process not in processes_map:
                print(f"Process '{specific_process}' not found in Procfile.")
                return
            processes_map = {specific_process: processes_map[specific_process]}

        if not processes_map:
            print("No processes to start.")
            return

        tasks = []
        # Assign colors for output prefixes
        colors = ["32", "33", "34", "35", "36", "31"] # Green, Yellow, Blue, Magenta, Cyan, Red

        print(f"Starting {len(processes_map)} process(es)...")
        print("Press Ctrl+C to stop.")

        running_procs = []

        try:
            for i, (name, command) in enumerate(processes_map.items()):
                color = colors[i % len(colors)]

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

                running_procs.append(process)
                self.processes[name] = process

                # Create tasks for streaming stdout and stderr
                tasks.append(asyncio.create_task(self._stream_output(name, process.stdout, color)))
                tasks.append(asyncio.create_task(self._stream_output(name, process.stderr, color)))

            # Wait for all processes to complete
            await asyncio.gather(*tasks)

        except asyncio.CancelledError:
            print("\nStopping processes...")
            for p in running_procs:
                try:
                    if sys.platform != "win32":
                        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                    else:
                        p.terminate()
                except ProcessLookupError:
                    pass
            # Wait for termination
            await asyncio.gather(*[p.wait() for p in running_procs])

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
            pass # Clean exit handled in start_processes
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
