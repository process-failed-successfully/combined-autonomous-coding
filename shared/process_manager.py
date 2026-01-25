import asyncio
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Deque
from collections import deque
from pathlib import Path

@dataclass
class ServiceInfo:
    name: str
    command: str
    cwd: Path
    status: str = "Stopped"  # "Running", "Stopped", "Error"
    pid: Optional[int] = None
    process: Optional[asyncio.subprocess.Process] = None
    output_buffer: Deque[str] = field(default_factory=lambda: deque(maxlen=1000))

class ServiceManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.services: Dict[str, ServiceInfo] = {}

    def add_service(self, name: str, command: str, cwd: Optional[Path] = None) -> None:
        """Registers a service without starting it."""
        if name in self.services:
            raise ValueError(f"Service '{name}' already exists.")

        self.services[name] = ServiceInfo(
            name=name,
            command=command,
            cwd=cwd or self.project_dir
        )

    async def start_service(self, name: str) -> None:
        """Starts a registered service."""
        if name not in self.services:
            raise ValueError(f"Service '{name}' not found.")

        service = self.services[name]
        if service.status == "Running":
            return

        try:
            # Create subprocess
            # We use shell=True via create_subprocess_shell to handle complex commands
            process = await asyncio.create_subprocess_shell(
                service.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT, # Merge stdout and stderr
                cwd=service.cwd
            )

            service.process = process
            service.pid = process.pid
            service.status = "Running"

            # Start output reader task
            asyncio.create_task(self._read_output(name, process))
            # Start waiter task to detect exit
            asyncio.create_task(self._wait_for_exit(name, process))

        except Exception as e:
            service.status = "Error"
            service.output_buffer.append(f"[System Error] {str(e)}")

    async def stop_service(self, name: str) -> None:
        """Stops a running service."""
        if name not in self.services:
            return

        service = self.services[name]
        if service.process and service.status == "Running":
            try:
                service.process.terminate()
                try:
                    await asyncio.wait_for(service.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    service.process.kill()
            except ProcessLookupError:
                pass # Already dead

            service.status = "Stopped"
            service.pid = None
            service.process = None

    async def restart_service(self, name: str) -> None:
        await self.stop_service(name)
        await self.start_service(name)

    async def _read_output(self, name: str, process: asyncio.subprocess.Process) -> None:
        """Reads output from the process stream."""
        service = self.services[name]
        if not process.stdout:
            return

        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').rstrip()
                service.output_buffer.append(decoded)
        except Exception:
            pass

    async def _wait_for_exit(self, name: str, process: asyncio.subprocess.Process) -> None:
        """Waits for process exit and updates status."""
        await process.wait()
        service = self.services[name]

        # Only update if it wasn't manually stopped (which might clear process ref)
        if service.process == process:
            service.status = "Stopped" if process.returncode == 0 else "Error"
            service.output_buffer.append(f"[System] Process exited with code {process.returncode}")
            service.pid = None
            service.process = None

    def get_service(self, name: str) -> Optional[ServiceInfo]:
        return self.services.get(name)

    def list_services(self) -> List[ServiceInfo]:
        return list(self.services.values())

    def get_latest_logs(self, name: str) -> List[str]:
        service = self.services.get(name)
        if not service:
            return []
        return list(service.output_buffer)
