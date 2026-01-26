import subprocess
import json
import asyncio
from typing import List, Dict, Optional

class DockerManager:
    def list_containers(self) -> List[Dict]:
        """Lists all containers (running and stopped)."""
        try:
            # We use a custom format to ensure valid JSON lines
            cmd = ["docker", "ps", "-a", "--format", "{{json .}}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    containers.append(json.loads(line))
            return containers
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []
        except json.JSONDecodeError:
            # Fallback or error handling
            return []

    def start_container(self, container_id: str) -> bool:
        """Starts a stopped container."""
        try:
            subprocess.run(["docker", "start", container_id], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def stop_container(self, container_id: str) -> bool:
        """Stops a running container."""
        try:
            subprocess.run(["docker", "stop", container_id], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def restart_container(self, container_id: str) -> bool:
        """Restarts a container."""
        try:
            subprocess.run(["docker", "restart", container_id], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_logs(self, container_id: str, tail: int = 100) -> str:
        """Fetches the last N lines of logs."""
        try:
            cmd = ["docker", "logs", "--tail", str(tail), container_id]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            return f"Error fetching logs: {e.stderr}"
        except FileNotFoundError:
            return "Error fetching logs: Docker not found"

    def inspect_container(self, container_id: str) -> Optional[Dict]:
        """Returns detailed inspection data."""
        try:
            cmd = ["docker", "inspect", container_id]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            if data:
                return data[0]
            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            return None
