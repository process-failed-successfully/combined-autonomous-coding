import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List


class HelmLabManager:
    """
    Manages Helm operations by wrapping the CLI.
    """
    def __init__(self, working_dir: Path = Path(".")):
        self.working_dir = working_dir
        self.executable = shutil.which("helm")

    def check_install(self) -> bool:
        """Checks if helm is installed."""
        return self.executable is not None

    def _run_command(self, args: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
        """Runs a helm command."""
        if not self.executable:
            # This should be handled by caller usually, but safe guard here
            raise FileNotFoundError("Helm executable not found. Please install helm.")

        cmd = [self.executable] + args
        try:
            # nosec: Subprocess call with trusted binary (checked via shutil.which)
            return subprocess.run(
                cmd,
                cwd=self.working_dir,
                check=False,
                text=True,
                capture_output=capture_output
            )  # nosec
        except Exception as e:
            print(f"Error executing command {' '.join(cmd)}: {e}", file=sys.stderr)
            raise

    def list_releases(self, all_namespaces: bool = False, namespace: Optional[str] = None) -> bool:
        """Lists releases."""
        args = ["list"]
        if all_namespaces:
            args.append("--all-namespaces")
        elif namespace:
            args.extend(["--namespace", namespace])

        result = self._run_command(args, capture_output=False)
        return result.returncode == 0

    def install_chart(self, release_name: str, chart: str, namespace: Optional[str] = None, values: Optional[str] = None, sets: Optional[List[str]] = None) -> bool:
        """Installs a chart."""
        args = ["install", release_name, chart]
        if namespace:
            args.extend(["--namespace", namespace])
        if values:
            args.extend(["--values", values])
        if sets:
            for s in sets:
                args.extend(["--set", s])

        result = self._run_command(args, capture_output=False)
        return result.returncode == 0

    def uninstall_release(self, release_name: str, namespace: Optional[str] = None) -> bool:
        """Uninstalls a release."""
        args = ["uninstall", release_name]
        if namespace:
            args.extend(["--namespace", namespace])

        result = self._run_command(args, capture_output=False)
        return result.returncode == 0

    def status_release(self, release_name: str, namespace: Optional[str] = None) -> bool:
        """Gets status of a release."""
        args = ["status", release_name]
        if namespace:
            args.extend(["--namespace", namespace])

        result = self._run_command(args, capture_output=False)
        return result.returncode == 0

    def repo_add(self, name: str, url: str) -> bool:
        """Adds a repo."""
        args = ["repo", "add", name, url]
        result = self._run_command(args, capture_output=False)
        return result.returncode == 0

    def repo_update(self) -> bool:
        """Updates repos."""
        args = ["repo", "update"]
        result = self._run_command(args, capture_output=False)
        return result.returncode == 0

    def repo_list(self) -> bool:
        """Lists repos."""
        args = ["repo", "list"]
        result = self._run_command(args, capture_output=False)
        return result.returncode == 0


def run_helm_lab_logic(args):
    """
    CLI entry point for Helm Lab.
    """
    project_dir = args.project_dir.resolve()
    manager = HelmLabManager(working_dir=project_dir)

    if not manager.check_install():
        print("❌ Error: 'helm' executable not found. Please install Helm.", file=sys.stderr)
        sys.exit(1)

    if args.action == "ls" or args.action == "list":
        success = manager.list_releases(all_namespaces=args.all, namespace=args.namespace)
        sys.exit(0 if success else 1)

    elif args.action == "install":
        success = manager.install_chart(
            release_name=args.name,
            chart=args.chart,
            namespace=args.namespace,
            values=args.values,
            sets=args.set
        )
        sys.exit(0 if success else 1)

    elif args.action == "uninstall":
        success = manager.uninstall_release(release_name=args.name, namespace=args.namespace)
        sys.exit(0 if success else 1)

    elif args.action == "status":
        success = manager.status_release(release_name=args.name, namespace=args.namespace)
        sys.exit(0 if success else 1)

    elif args.action == "repo":
        if args.subaction == "add":
            if not args.name or not args.url:
                print("Error: Name and URL required for repo add.", file=sys.stderr)
                sys.exit(1)
            success = manager.repo_add(name=args.name, url=args.url)
        elif args.subaction == "update":
            success = manager.repo_update()
        elif args.subaction == "list":
            success = manager.repo_list()
        else:
            print(f"Unknown repo action: {args.subaction}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0 if success else 1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
