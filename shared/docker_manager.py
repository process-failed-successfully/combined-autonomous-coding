import subprocess
import json
import asyncio
from typing import List, Dict, Optional, Union

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

    def list_images(self) -> List[Dict]:
        """Lists all images."""
        try:
            cmd = ["docker", "images", "--format", "{{json .}}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            images = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    images.append(json.loads(line))
            return images
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []
        except json.JSONDecodeError:
            return []

    def start_container(self, container_id: str) -> bool:
        """Starts a stopped container."""
        try:
            subprocess.run(["docker", "start", container_id], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def stop_container(self, container_id: str) -> bool:
        """Stops a running container."""
        try:
            subprocess.run(["docker", "stop", container_id], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def restart_container(self, container_id: str) -> bool:
        """Restarts a container."""
        try:
            subprocess.run(["docker", "restart", container_id], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """Removes a container."""
        try:
            cmd = ["docker", "rm"]
            if force:
                cmd.append("-f")
            cmd.append(container_id)
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def remove_image(self, image_id: str, force: bool = False) -> bool:
        """Removes an image."""
        try:
            cmd = ["docker", "rmi"]
            if force:
                cmd.append("-f")
            cmd.append(image_id)
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def prune_containers(self) -> bool:
        """Prunes stopped containers (always forced)."""
        try:
            # Always use -f to avoid interactive prompt which hangs subprocess
            cmd = ["docker", "container", "prune", "-f"]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def prune_images(self) -> bool:
        """Prunes unused images (always forced)."""
        try:
            # Always use -f to avoid interactive prompt which hangs subprocess
            cmd = ["docker", "image", "prune", "-f"]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_logs(self, container_id: str, tail: int = 100) -> str:
        """Fetches the last N lines of logs."""
        try:
            cmd = ["docker", "logs", "--tail", str(tail), container_id]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            return f"Error fetching logs: {e.stderr}"

    def inspect_container(self, container_id: str) -> Optional[Dict]:
        """Returns detailed inspection data."""
        try:
            cmd = ["docker", "inspect", container_id]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            if data:
                return data[0]
            return None
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return None

    def get_stats(self, container_id: str) -> Optional[Dict]:
        """
        Returns stats for a container.
        Note: 'docker stats' behavior with --format {{json .}} depends on version.
        We use --no-stream to get a single snapshot.
        """
        try:
            cmd = ["docker", "stats", "--no-stream", "--format", "{{json .}}", container_id]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            return None
