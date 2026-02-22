import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

class AnsibleManager:
    """
    Manages Ansible operations by wrapping the CLI tools.
    """
    def __init__(self, working_dir: Path = Path(".")):
        self.working_dir = working_dir
        self.playbook_cmd = shutil.which("ansible-playbook")
        self.inventory_cmd = shutil.which("ansible-inventory")
        self.lint_cmd = shutil.which("ansible-lint")
        self.doc_cmd = shutil.which("ansible-doc")
        self.galaxy_cmd = shutil.which("ansible-galaxy")

    def check_install(self) -> bool:
        """Checks if ansible-playbook is installed."""
        return self.playbook_cmd is not None

    def _run_command(self, cmd: List[str], capture_output: bool = False, check: bool = False) -> subprocess.CompletedProcess:
        """Runs an ansible command."""
        try:
            return subprocess.run(
                cmd,
                cwd=self.working_dir,
                check=check,
                text=True,
                capture_output=capture_output
            )
        except Exception as e:
            print(f"Error executing command {' '.join(cmd)}: {e}", file=sys.stderr)
            raise

    def run_playbook(self, playbook: str, inventory: Optional[str] = None, check_mode: bool = False, diff_mode: bool = False, limit: Optional[str] = None, extra_vars: Optional[str] = None, capture_output: bool = False) -> Any:
        """Runs an ansible playbook."""
        if not self.playbook_cmd:
             msg = "Error: ansible-playbook not found. Please install ansible."
             if capture_output: return (False, msg)
             print(msg, file=sys.stderr)
             return False

        args = [self.playbook_cmd, playbook]
        if inventory:
            args.extend(["-i", inventory])
        if check_mode:
            args.append("--check")
        if diff_mode:
            args.append("--diff")
        if limit:
            args.extend(["--limit", limit])
        if extra_vars:
            args.extend(["--extra-vars", extra_vars])

        if not capture_output:
            print(f"Running: {' '.join(args)}")

        result = self._run_command(args, capture_output=capture_output)

        if capture_output:
            output = (result.stdout or "") + (result.stderr or "")
            return (result.returncode == 0, output)
        return result.returncode == 0

    def lint(self, path: Optional[str] = None, capture_output: bool = False) -> Any:
        """Runs ansible-lint."""
        if not self.lint_cmd:
             msg = "Error: ansible-lint not found. Please install it (pip install ansible-lint)."
             if capture_output: return (False, msg)
             print(msg, file=sys.stderr)
             return False

        target = path if path else "."
        args = [self.lint_cmd, target]
        if not capture_output:
            print(f"Running ansible-lint on {target}...")

        result = self._run_command(args, capture_output=capture_output)

        if capture_output:
            output = (result.stdout or "") + (result.stderr or "")
            return (result.returncode == 0, output)
        return result.returncode == 0

    def list_inventory(self, inventory: Optional[str] = None) -> Optional[str]:
        """Lists inventory as JSON."""
        if not self.inventory_cmd:
             print("Error: ansible-inventory not found.", file=sys.stderr)
             return None

        args = [self.inventory_cmd, "--list"]
        if inventory:
            args.extend(["-i", inventory])

        result = self._run_command(args, capture_output=True)
        if result.returncode == 0:
            return result.stdout
        else:
             print(f"Error listing inventory: {result.stderr}", file=sys.stderr)
             return None

    def show_doc(self, module: str) -> bool:
        """Shows documentation for a module."""
        if not self.doc_cmd:
             print("Error: ansible-doc not found.", file=sys.stderr)
             return False

        args = [self.doc_cmd, module]
        result = self._run_command(args)
        return result.returncode == 0

    def init_structure(self, project_name: Optional[str] = None) -> bool:
        """Scaffolds a basic Ansible directory structure."""
        base_dir = self.working_dir
        if project_name:
            base_dir = base_dir / project_name
            base_dir.mkdir(parents=True, exist_ok=True)

        # Create directories
        dirs = ["inventory", "roles", "playbooks", "group_vars", "host_vars"]
        for d in dirs:
            (base_dir / d).mkdir(exist_ok=True)

        # Create default files
        cfg_path = base_dir / "ansible.cfg"
        if not cfg_path.exists():
            cfg_path.write_text("[defaults]\ninventory = ./inventory/hosts\nroles_path = ./roles\n")

        inv_path = base_dir / "inventory/hosts"
        if not inv_path.exists():
            inv_path.write_text("[local]\nlocalhost ansible_connection=local\n")

        pb_path = base_dir / "playbooks/site.yml"
        if not pb_path.exists():
            pb_path.write_text("---\n- hosts: local\n  tasks:\n    - debug:\n        msg: 'Hello Ansible'\n")

        print(f"Initialized Ansible project structure in {base_dir}")
        return True


def run_ansible_lab_logic(args):
    """
    CLI logic for Ansible Lab.
    """
    project_dir = Path(args.project_dir).resolve()
    manager = AnsibleManager(working_dir=project_dir)

    if args.action == "playbook":
        success = manager.run_playbook(
            playbook=args.playbook,
            inventory=args.inventory,
            check_mode=args.check,
            diff_mode=args.diff,
            limit=args.limit,
            extra_vars=args.extra_vars
        )
        sys.exit(0 if success else 1)

    elif args.action == "lint":
        success = manager.lint(path=args.path)
        sys.exit(0 if success else 1)

    elif args.action == "inventory":
        output = manager.list_inventory(inventory=args.inventory)
        if output:
            print(output)
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "doc":
        success = manager.show_doc(module=args.module)
        sys.exit(0 if success else 1)

    elif args.action == "init":
        success = manager.init_structure(project_name=args.name)
        sys.exit(0 if success else 1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
