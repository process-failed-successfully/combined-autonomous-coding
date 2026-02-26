import requests
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

class GoLabManager:
    """Manages Go Lab operations: info, versions, init, tidy, install."""

    PROXY_URL = "https://proxy.golang.org"

    def __init__(self, project_dir: Path = Path(".")):
        self.project_dir = Path(project_dir)

    def _get_json(self, url: str) -> Dict[str, Any]:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Resource not found: {url}")
            raise
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {e}")

    def _get_text(self, url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Resource not found: {url}")
            raise
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {e}")

    def get_latest_version(self, package: str) -> Dict[str, Any]:
        """Fetches the latest version info from the Go Proxy."""
        # Go Proxy API: /<module>/@latest
        url = f"{self.PROXY_URL}/{package}/@latest"
        return self._get_json(url)

    def get_versions(self, package: str) -> List[str]:
        """Fetches a list of versions from the Go Proxy."""
        # Go Proxy API: /<module>/@v/list
        url = f"{self.PROXY_URL}/{package}/@v/list"
        text = self._get_text(url)
        return [v for v in text.splitlines() if v.strip()]

    def init_mod(self, module_name: str) -> bool:
        """Wraps `go mod init <module_name>`."""
        try:
            subprocess.run(["go", "mod", "init", module_name], cwd=self.project_dir, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error initializing module: {e}", file=sys.stderr)
            return False
        except FileNotFoundError:
            print("Error: 'go' command not found.", file=sys.stderr)
            return False

    def tidy(self) -> bool:
        """Wraps `go mod tidy`."""
        try:
            subprocess.run(["go", "mod", "tidy"], cwd=self.project_dir, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running go mod tidy: {e}", file=sys.stderr)
            return False
        except FileNotFoundError:
            print("Error: 'go' command not found.", file=sys.stderr)
            return False

    def install(self, package: str) -> bool:
        """Wraps `go get <package>`."""
        try:
            subprocess.run(["go", "get", package], cwd=self.project_dir, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing package {package}: {e}", file=sys.stderr)
            return False
        except FileNotFoundError:
            print("Error: 'go' command not found.", file=sys.stderr)
            return False

    def get_mod_file(self) -> Optional[str]:
        """Reads the go.mod file."""
        mod_path = self.project_dir / "go.mod"
        if mod_path.exists():
            return mod_path.read_text(encoding="utf-8")
        return None

def run_go_lab_logic(args) -> bool:
    """CLI handler for Go Lab."""
    manager = GoLabManager(args.project_dir)

    try:
        if args.action == "info":
            if not args.package:
                print("Error: --package required for 'info'.", file=sys.stderr)
                return False
            info = manager.get_latest_version(args.package)
            print(f"--- {args.package} (Latest) ---")
            print(f"Version: {info.get('Version')}")
            print(f"Time:    {info.get('Time')}")
            return True

        elif args.action == "versions":
            if not args.package:
                print("Error: --package required for 'versions'.", file=sys.stderr)
                return False
            versions = manager.get_versions(args.package)
            print(f"--- Versions for {args.package} ---")
            for v in versions:
                print(v)
            return True

        elif args.action == "init":
            if not args.module_name:
                print("Error: --module-name required for 'init'.", file=sys.stderr)
                return False
            if manager.init_mod(args.module_name):
                print(f"Initialized module: {args.module_name}")
                return True
            else:
                return False

        elif args.action == "tidy":
            if manager.tidy():
                print("Go module tidied.")
                return True
            else:
                return False

        elif args.action == "install":
            if not args.package:
                print("Error: --package required for 'install'.", file=sys.stderr)
                return False
            if manager.install(args.package):
                print(f"Installed {args.package}")
                return True
            else:
                return False

        elif args.action == "mod":
            content = manager.get_mod_file()
            if content:
                print("--- go.mod ---")
                print(content)
            else:
                print("No go.mod file found.")
            return True

        else:
            print(f"Unknown action: {args.action}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
