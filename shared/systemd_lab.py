import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

class SystemdManager:
    """
    Manages systemd units (generation, control, status).
    """

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")
        self.systemctl_path = shutil.which("systemctl")
        self.journalctl_path = shutil.which("journalctl")

    def _check_systemd(self):
        if not self.systemctl_path:
            raise EnvironmentError("systemctl not found. Is this a systemd-based system?")

    def generate_unit_file(self,
                           name: str,
                           command: str,
                           user: str = "root",
                           working_dir: Optional[str] = None,
                           description: Optional[str] = None,
                           environment: Optional[Dict[str, str]] = None,
                           restart_policy: str = "always",
                           service_type: str = "simple") -> str:
        """
        Generates the content of a systemd .service file.
        """
        if not description:
            description = f"Systemd service for {name}"

        if not working_dir:
            working_dir = str(self.project_dir.resolve())

        content = [
            "[Unit]",
            f"Description={description}",
            "After=network.target",
            "",
            "[Service]",
            f"Type={service_type}",
            f"User={user}",
            f"WorkingDirectory={working_dir}",
            f"ExecStart={command}",
            f"Restart={restart_policy}",
        ]

        if environment:
            for k, v in environment.items():
                content.append(f"Environment={k}={v}")

        content.append("")
        content.append("[Install]")
        content.append("WantedBy=multi-user.target")

        return "\n".join(content)

    def list_units(self, pattern: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Lists active service units.
        Wraps `systemctl list-units --type=service --no-pager --no-legend`.
        """
        self._check_systemd()
        cmd = [self.systemctl_path, "list-units", "--type=service", "--no-pager", "--no-legend"]
        if pattern:
            cmd.append(pattern)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            units = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split(maxsplit=4)
                if len(parts) >= 4:
                    units.append({
                        "unit": parts[0],
                        "load": parts[1],
                        "active": parts[2],
                        "sub": parts[3],
                        "description": parts[4] if len(parts) > 4 else ""
                    })
            return units
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to list units: {e.stderr.strip()}")

    def get_status(self, name: str) -> str:
        """
        Gets the full status output of a service.
        Wraps `systemctl status name`.
        """
        self._check_systemd()
        # systemctl status returns non-zero if service is not running, but we want the output
        cmd = [self.systemctl_path, "status", name, "--no-pager"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip() if result.stdout else result.stderr.strip()

    def control_service(self, name: str, action: str) -> Tuple[bool, str]:
        """
        Controls a service (start, stop, restart, enable, disable).
        Returns (success, message).
        """
        self._check_systemd()
        valid_actions = ["start", "stop", "restart", "enable", "disable", "reload"]
        if action not in valid_actions:
            raise ValueError(f"Invalid action: {action}")

        cmd = [self.systemctl_path, action, name]
        try:
            # Requires root usually, so this might fail if not run as sudo
            # We don't use sudo here, we rely on user running script as sudo if needed
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return True, f"Service {name} {action}ed successfully."
        except subprocess.CalledProcessError as e:
            return False, f"Failed to {action} {name}: {e.stderr.strip()}"

    def get_logs(self, name: str, lines: int = 50) -> str:
        """
        Gets logs for a service.
        Wraps `journalctl -u name -n lines --no-pager`.
        """
        if not self.journalctl_path:
             raise EnvironmentError("journalctl not found.")

        cmd = [self.journalctl_path, "-u", name, "-n", str(lines), "--no-pager"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
             raise RuntimeError(f"Failed to get logs: {e.stderr.strip()}")


def run_systemd_lab_logic(args):
    """
    CLI entry point for Systemd Lab.
    """
    manager = SystemdManager(args.project_dir)

    # 1. GENERATE
    if args.action == "generate":
        # Resolve command (absolute path is better)
        cmd = args.cmd
        # If user provided a relative path to a script in project dir, verify existence
        if cmd and not cmd.startswith("/"):
             script_path = (args.project_dir / cmd).resolve()
             if script_path.exists():
                 cmd = str(script_path)

        # Parse env vars (key=value,key=value)
        env_dict = {}
        if args.env:
            for pair in args.env.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    env_dict[k.strip()] = v.strip()

        content = manager.generate_unit_file(
            name=args.name,
            command=cmd,
            user=args.user,
            working_dir=args.workdir,
            description=args.description,
            environment=env_dict,
            restart_policy=args.restart,
            service_type=args.type
        )

        if args.output:
            out_path = Path(args.output).resolve()
            try:
                out_path.write_text(content)
                print(f"✅ Generated unit file at: {out_path}")
            except IOError as e:
                print(f"❌ Error writing file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(content)
        sys.exit(0)

    # 2. LIST
    elif args.action == "list":
        try:
            units = manager.list_units(args.pattern)
            if not units:
                print("No matching units found.")
                sys.exit(0)

            print(f"{'UNIT':<40} | {'LOAD':<10} | {'ACTIVE':<10} | {'SUB':<10} | {'DESCRIPTION'}")
            print("-" * 100)
            for u in units:
                print(f"{u['unit']:<40} | {u['load']:<10} | {u['active']:<10} | {u['sub']:<10} | {u['description']}")
        except EnvironmentError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    # 3. STATUS
    elif args.action == "status":
        if not args.name:
             print("Error: Service name required.", file=sys.stderr)
             sys.exit(1)
        try:
            print(manager.get_status(args.name))
        except EnvironmentError as e:
             print(f"❌ {e}", file=sys.stderr)
             sys.exit(1)

    # 4. CONTROL (Start, Stop, etc)
    elif args.action in ["start", "stop", "restart", "enable", "disable"]:
        if not args.name:
             print("Error: Service name required.", file=sys.stderr)
             sys.exit(1)

        try:
            success, msg = manager.control_service(args.name, args.action)
            if success:
                print(f"✅ {msg}")
            else:
                print(f"❌ {msg}", file=sys.stderr)
                sys.exit(1)
        except EnvironmentError as e:
             print(f"❌ {e}", file=sys.stderr)
             sys.exit(1)
        except Exception as e:
             print(f"❌ Error: {e}", file=sys.stderr)
             sys.exit(1)

    # 5. LOGS
    elif args.action == "logs":
        if not args.name:
             print("Error: Service name required.", file=sys.stderr)
             sys.exit(1)

        try:
            print(manager.get_logs(args.name, args.lines))
        except EnvironmentError as e:
             print(f"❌ {e}", file=sys.stderr)
             sys.exit(1)
        except Exception as e:
             print(f"❌ Error: {e}", file=sys.stderr)
             sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
