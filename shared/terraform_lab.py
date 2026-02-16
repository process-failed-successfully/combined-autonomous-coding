import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List


class TerraformManager:
    """
    Manages Terraform operations by wrapping the CLI.
    """
    def __init__(self, working_dir: Path = Path(".")):
        self.working_dir = working_dir
        self.executable = shutil.which("terraform")

    def check_install(self) -> bool:
        """Checks if terraform is installed."""
        return self.executable is not None

    def _run_command(self, args: List[str], capture_output: bool = False) -> "subprocess.CompletedProcess[str]":
        """Runs a terraform command."""
        executable = self.executable
        if not executable:
            raise FileNotFoundError("Terraform executable not found. Please install terraform.")

        cmd = [executable] + args
        try:
            return subprocess.run(
                cmd,
                cwd=self.working_dir,
                check=False,  # We handle return codes manually
                text=True,
                capture_output=capture_output
            )
        except Exception as e:
            print(f"Error executing command {' '.join(cmd)}: {e}", file=sys.stderr)
            raise

    def init(self, upgrade: bool = False) -> bool:
        """Initializes the terraform working directory."""
        args = ["init"]
        if upgrade:
            args.append("-upgrade")

        print(f"Running 'terraform init' in {self.working_dir}...")
        result = self._run_command(args)
        return result.returncode == 0

    def plan(self, out_file: Optional[str] = None) -> bool:
        """Generates a terraform execution plan."""
        args = ["plan"]
        if out_file:
            args.extend(["-out", out_file])

        print(f"Running 'terraform plan' in {self.working_dir}...")
        result = self._run_command(args)
        return result.returncode == 0

    def apply(self, auto_approve: bool = False, plan_file: Optional[str] = None) -> bool:
        """Applies the changes."""
        args = ["apply"]
        if plan_file:
            args.append(plan_file)
        elif auto_approve:
            args.append("-auto-approve")

        print(f"Running 'terraform apply' in {self.working_dir}...")
        result = self._run_command(args)
        return result.returncode == 0

    def destroy(self, auto_approve: bool = False) -> bool:
        """Destroys the infrastructure."""
        args = ["destroy"]
        if auto_approve:
            args.append("-auto-approve")

        print(f"Running 'terraform destroy' in {self.working_dir}...")
        result = self._run_command(args)
        return result.returncode == 0

    def validate(self) -> bool:
        """Validates the configuration."""
        print(f"Running 'terraform validate' in {self.working_dir}...")
        result = self._run_command(["validate"])
        return result.returncode == 0

    def fmt(self, check: bool = False, recursive: bool = False) -> bool:
        """Formats the configuration files."""
        args = ["fmt"]
        if check:
            args.append("-check")
        if recursive:
            args.append("-recursive")

        print(f"Running 'terraform fmt' in {self.working_dir}...")
        result = self._run_command(args)
        return result.returncode == 0

    def output(self, json_format: bool = False) -> Optional[str]:
        """Reads output variables."""
        args = ["output"]
        if json_format:
            args.append("-json")

        result = self._run_command(args, capture_output=True)
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"Error reading output: {result.stderr}", file=sys.stderr)
            return None

    def show(self, plan_file: Optional[str] = None, json_format: bool = False) -> Optional[str]:
        """Shows state or plan."""
        args = ["show"]
        if json_format:
            args.append("-json")
        if plan_file:
            args.append(plan_file)

        result = self._run_command(args, capture_output=True)
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"Error running show: {result.stderr}", file=sys.stderr)
            return None


def run_terraform_lab_logic(args):
    """
    CLI entry point for Terraform Lab.
    """
    project_dir = args.project_dir.resolve()
    # If the user is running from root but wants to target a subdir, they can pass it via cwd or just run from there
    # But usually args.project_dir is what we use.

    # Check if a specific working directory for terraform was requested via arguments if added later
    # For now we use project_dir

    manager = TerraformManager(working_dir=project_dir)

    if not manager.check_install():
        print("❌ Error: 'terraform' executable not found. Please install Terraform.", file=sys.stderr)
        sys.exit(1)

    if args.action == "init":
        success = manager.init(upgrade=args.upgrade)
        sys.exit(0 if success else 1)

    elif args.action == "plan":
        success = manager.plan(out_file=args.out)
        sys.exit(0 if success else 1)

    elif args.action == "apply":
        success = manager.apply(auto_approve=args.auto_approve, plan_file=args.plan_file)
        sys.exit(0 if success else 1)

    elif args.action == "destroy":
        success = manager.destroy(auto_approve=args.auto_approve)
        sys.exit(0 if success else 1)

    elif args.action == "validate":
        success = manager.validate()
        sys.exit(0 if success else 1)

    elif args.action == "fmt":
        success = manager.fmt(check=args.check, recursive=args.recursive)
        sys.exit(0 if success else 1)

    elif args.action == "output":
        output = manager.output(json_format=args.json)
        if output:
            print(output)
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "show":
        output = manager.show(plan_file=args.plan_file, json_format=args.json)
        if output:
            print(output)
            sys.exit(0)
        else:
            sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
