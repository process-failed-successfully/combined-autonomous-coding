import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

class SshLabManager:
    """
    Manages SSH keys and configuration.
    """
    def __init__(self, ssh_dir: Optional[Path] = None):
        if ssh_dir:
            self.ssh_dir = ssh_dir
        else:
            self.ssh_dir = Path.home() / ".ssh"

        self.config_path = self.ssh_dir / "config"

    def ensure_ssh_dir(self):
        """Ensures the .ssh directory exists."""
        if not self.ssh_dir.exists():
            self.ssh_dir.mkdir(mode=0o700, parents=True)

    def list_keys(self) -> List[Dict[str, Any]]:
        """
        Lists SSH keys in the directory.
        """
        if not self.ssh_dir.exists():
            return []

        keys = []
        for item in self.ssh_dir.iterdir():
            if item.is_file() and not item.name.endswith(".pub") and not item.name == "config" and not item.name == "known_hosts":
                # Check if corresponding .pub exists
                pub_key = item.with_suffix(".pub")
                has_pub = pub_key.exists()
                keys.append({
                    "name": item.name,
                    "path": str(item),
                    "has_pub": has_pub
                })
        return keys

    def generate_key(self, key_type: str, bits: int, comment: str, filename: str) -> Dict[str, Any]:
        """
        Generates a new SSH key using ssh-keygen.
        """
        self.ensure_ssh_dir()
        key_path = self.ssh_dir / filename

        if key_path.exists():
            return {"success": False, "error": f"Key '{filename}' already exists."}

        cmd = [
            "ssh-keygen",
            "-t", key_type,
            "-b", str(bits),
            "-C", comment,
            "-f", str(key_path),
            "-N", "" # No passphrase for automation/lab purposes by default, though risky for real use
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return {"success": True, "path": str(key_path)}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": e.stderr}
        except FileNotFoundError:
            return {"success": False, "error": "ssh-keygen command not found."}

    def get_fingerprint(self, filename: str) -> Dict[str, Any]:
        """
        Gets the fingerprint of a key.
        """
        key_path = self.ssh_dir / filename
        if not key_path.exists():
             return {"success": False, "error": f"Key '{filename}' not found."}

        cmd = ["ssh-keygen", "-l", "-f", str(key_path)]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return {"success": True, "fingerprint": result.stdout.strip()}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": e.stderr}

    def list_hosts(self) -> List[Dict[str, str]]:
        """
        Parses ~/.ssh/config to list defined hosts.
        """
        if not self.config_path.exists():
            return []

        hosts = []
        current_host: Dict[str, str] = {}

        try:
            with open(self.config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split(maxsplit=1)
                    if len(parts) != 2:
                        continue

                    key, value = parts
                    if key.lower() == 'host':
                        if current_host:
                            hosts.append(current_host)
                        current_host = {'Host': value}
                    elif current_host:
                        current_host[key] = value

                if current_host:
                    hosts.append(current_host)
        except Exception as e:
            print(f"Error reading config: {e}", file=sys.stderr)

        return hosts

    def add_host(self, host: str, hostname: str, user: str, identity_file: Optional[str] = None) -> bool:
        """
        Appends a new host to ~/.ssh/config.
        """
        self.ensure_ssh_dir()

        entry = f"\nHost {host}\n    HostName {hostname}\n    User {user}\n"
        if identity_file:
            # Expand ~ if present
            if identity_file.startswith("~"):
                identity_file = os.path.expanduser(identity_file)
            entry += f"    IdentityFile {identity_file}\n"

        try:
            with open(self.config_path, 'a') as f:
                f.write(entry)
            return True
        except Exception as e:
            print(f"Error writing to config: {e}", file=sys.stderr)
            return False

def run_ssh_lab_logic(args):
    """
    CLI entry point for SSH Lab.
    """
    manager = SshLabManager() # Defaults to ~/.ssh

    if args.action == "list":
        keys = manager.list_keys()
        if not keys:
            print(f"No keys found in {manager.ssh_dir}")
            sys.exit(0)

        print(f"--- SSH Keys in {manager.ssh_dir} ---")
        print(f"{'Name':<20} | {'Pub Key?'}")
        print("-" * 35)
        for k in keys:
            pub = "Yes" if k['has_pub'] else "No"
            print(f"{k['name']:<20} | {pub}")

    elif args.action == "keygen":
        if not args.filename:
            print("Error: --filename is required.", file=sys.stderr)
            sys.exit(1)

        print(f"Generating {args.type} key ({args.bits} bits)...")
        result = manager.generate_key(args.type, args.bits, args.comment, args.filename)

        if result["success"]:
            print(f"✅ Key generated at: {result['path']}")
        else:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "fingerprint":
        if not args.filename:
            print("Error: --filename is required.", file=sys.stderr)
            sys.exit(1)

        result = manager.get_fingerprint(args.filename)
        if result["success"]:
            print(result["fingerprint"])
        else:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "config":
        if args.sub_action == "list":
            hosts = manager.list_hosts()
            if not hosts:
                print("No hosts defined in config.")
                sys.exit(0)

            print(f"--- SSH Hosts ({len(hosts)}) ---")
            for h in hosts:
                print(f"Host: {h.get('Host')}")
                if 'HostName' in h: print(f"  HostName: {h['HostName']}")
                if 'User' in h: print(f"  User: {h['User']}")
                if 'IdentityFile' in h: print(f"  IdentityFile: {h['IdentityFile']}")
                print("")

        elif args.sub_action == "add":
            if not args.host or not args.hostname or not args.user:
                print("Error: --host, --hostname, and --user are required.", file=sys.stderr)
                sys.exit(1)

            success = manager.add_host(args.host, args.hostname, args.user, args.identity)
            if success:
                print(f"✅ Host '{args.host}' added to config.")
            else:
                sys.exit(1)

    sys.exit(0)
