import subprocess
import json
import shutil
from typing import List, Dict, Optional, Union, Any

class K8sManager:
    """
    Manages interactions with a Kubernetes cluster using kubectl.
    """

    def __init__(self):
        self.kubectl_path = shutil.which("kubectl")

    def check_kubectl_installed(self) -> bool:
        """Checks if kubectl is installed and available in PATH."""
        return self.kubectl_path is not None

    def _run_command(self, cmd: List[str], capture_output: bool = True, text: bool = True) -> subprocess.CompletedProcess:
        """Helper to run kubectl commands."""
        if not self.kubectl_path:
            raise FileNotFoundError("kubectl not found. Please install it.")

        full_cmd = [self.kubectl_path] + cmd
        return subprocess.run(full_cmd, capture_output=capture_output, text=text, check=True)

    def get_version(self) -> Dict[str, Any]:
        """Gets client and server version info."""
        try:
            # --client only to avoid connecting if cluster is down, but we want server info if possible.
            # We'll try full version first.
            cmd = ["version", "--output=json"]
            result = self._run_command(cmd)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError:
            # Fallback to client version only if server is unreachable
            try:
                cmd = ["version", "--client", "--output=json"]
                result = self._run_command(cmd)
                return json.loads(result.stdout)
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                return {}

    def get_cluster_info(self) -> str:
        """Gets cluster info."""
        try:
            result = self._run_command(["cluster-info"])
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error getting cluster info: {e.stderr}"

    def list_pods(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists pods in a namespace (or all namespaces)."""
        try:
            cmd = ["get", "pods", "-o", "json"]
            if namespace:
                cmd.extend(["-n", namespace])
            else:
                cmd.append("--all-namespaces")

            result = self._run_command(cmd)
            data = json.loads(result.stdout)
            return data.get("items", [])
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

    def list_namespaces(self) -> List[Dict[str, Any]]:
        """Lists all namespaces."""
        try:
            cmd = ["get", "namespaces", "-o", "json"]
            result = self._run_command(cmd)
            data = json.loads(result.stdout)
            return data.get("items", [])
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

    def list_deployments(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists deployments."""
        try:
            cmd = ["get", "deployments", "-o", "json"]
            if namespace:
                cmd.extend(["-n", namespace])
            else:
                cmd.append("--all-namespaces")

            result = self._run_command(cmd)
            data = json.loads(result.stdout)
            return data.get("items", [])
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

    def list_services(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists services."""
        try:
            cmd = ["get", "services", "-o", "json"]
            if namespace:
                cmd.extend(["-n", namespace])
            else:
                cmd.append("--all-namespaces")

            result = self._run_command(cmd)
            data = json.loads(result.stdout)
            return data.get("items", [])
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

    def list_contexts(self) -> List[Dict[str, Any]]:
        """Lists available contexts."""
        try:
            # We use 'config view' to get structured context data
            cmd = ["config", "view", "-o", "json"]
            result = self._run_command(cmd)
            data = json.loads(result.stdout)
            contexts = data.get("contexts", [])
            current_context = data.get("current-context", "")

            # Enrich with 'current' flag
            for ctx in contexts:
                ctx["current"] = (ctx["name"] == current_context)
            return contexts
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

    def use_context(self, context_name: str) -> bool:
        """Switches the current context."""
        try:
            self._run_command(["config", "use-context", context_name])
            return True
        except subprocess.CalledProcessError:
            return False

    def get_logs(self, pod_name: str, namespace: Optional[str] = None, tail: int = 100) -> str:
        """Gets logs for a pod."""
        try:
            cmd = ["logs", pod_name, f"--tail={tail}"]
            if namespace:
                cmd.extend(["-n", namespace])

            result = self._run_command(cmd)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error getting logs: {e.stderr}"

    def describe_resource(self, resource_type: str, name: str, namespace: Optional[str] = None) -> str:
        """Describes a resource."""
        try:
            cmd = ["describe", resource_type, name]
            if namespace:
                cmd.extend(["-n", namespace])

            result = self._run_command(cmd)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error describing resource: {e.stderr}"

    def apply_file(self, file_path: str) -> str:
        """Applies a configuration file."""
        try:
            cmd = ["apply", "-f", file_path]
            result = self._run_command(cmd)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error applying file: {e.stderr}"

    def delete_resource(self, resource_type: str, name: str, namespace: Optional[str] = None) -> str:
        """Deletes a resource."""
        try:
            cmd = ["delete", resource_type, name]
            if namespace:
                cmd.extend(["-n", namespace])

            result = self._run_command(cmd)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error deleting resource: {e.stderr}"
