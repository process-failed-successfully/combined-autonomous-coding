import shutil
import sys
import socket
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import os

class HostLabManager:
    """
    Manages entries in the /etc/hosts file (or custom path).
    """
    def __init__(self, hosts_file: Path):
        self.hosts_file = hosts_file

    def _is_valid_ip(self, ip: str) -> bool:
        """Validates IP address format."""
        try:
            socket.inet_pton(socket.AF_INET, ip)
            return True
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, ip)
                return True
            except socket.error:
                return False

    def list_entries(self) -> List[Dict[str, Any]]:
        """Parses the hosts file and returns a list of entries."""
        entries = []
        if not self.hosts_file.exists():
            return entries

        try:
            with open(self.hosts_file, 'r') as f:
                for i, line in enumerate(f):
                    raw_line = line.rstrip()
                    stripped = raw_line.lstrip()

                    if not stripped or stripped.startswith('#'):
                        # Check if it's a commented-out entry we manage
                        # Heuristic: # <IP> <HOST> ...
                        clean = stripped.lstrip('#').strip()
                        parts = clean.split()
                        if len(parts) >= 2 and self._is_valid_ip(parts[0]):
                            entries.append({
                                'type': 'entry',
                                'ip': parts[0],
                                'hosts': parts[1:],
                                'enabled': False,
                                'line_num': i + 1,
                                'raw': raw_line
                            })
                        else:
                            entries.append({
                                'type': 'comment',
                                'raw': raw_line,
                                'line_num': i + 1
                            })
                        continue

                    # Active entry
                    parts = stripped.split()
                    # Extract comment if present (e.g. 1.2.3.4 host # comment)
                    comment = None
                    ip_host_parts = []
                    for part in parts:
                        if part.startswith('#'):
                            comment = stripped[stripped.index('#')+1:].strip()
                            break
                        ip_host_parts.append(part)

                    if len(ip_host_parts) >= 2 and self._is_valid_ip(ip_host_parts[0]):
                        entries.append({
                            'type': 'entry',
                            'ip': ip_host_parts[0],
                            'hosts': ip_host_parts[1:],
                            'enabled': True,
                            'comment': comment,
                            'line_num': i + 1,
                            'raw': raw_line
                        })
                    else:
                        entries.append({
                            'type': 'comment', # Malformed or unknown line
                            'raw': raw_line,
                            'line_num': i + 1
                        })
        except PermissionError:
             print(f"❌ Permission denied reading {self.hosts_file}.", file=sys.stderr)
             return []
        except Exception as e:
             print(f"❌ Error reading hosts file: {e}", file=sys.stderr)
             return []

        return entries

    def add_entry(self, ip: str, host: str, comment: Optional[str] = None) -> bool:
        """Adds a new host entry."""
        if not self._is_valid_ip(ip):
            print(f"❌ Invalid IP address: {ip}", file=sys.stderr)
            return False

        # Check for duplicate host
        entries = self.list_entries()
        for e in entries:
            if e['type'] == 'entry' and host in e['hosts']:
                 print(f"⚠️  Host '{host}' already exists (IP: {e['ip']}).", file=sys.stderr)
                 return False

        line = f"{ip}\t{host}"
        if comment:
            line += f"\t# {comment}"

        try:
            # Ensure parent dir exists (for custom paths)
            self.hosts_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.hosts_file, 'a') as f:
                if self.hosts_file.stat().st_size > 0:
                     # Check if last char is newline
                     with open(self.hosts_file, 'rb') as fr:
                         fr.seek(-1, 2)
                         if fr.read(1) != b'\n':
                             f.write('\n')
                f.write(f"{line}\n")
            return True
        except PermissionError:
            print(f"❌ Permission denied writing to {self.hosts_file}. Try running with sudo.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ Error adding entry: {e}", file=sys.stderr)
            return False

    def remove_entry(self, host: str) -> bool:
        """Removes an entry by hostname (comments it out or deletes line)."""
        lines = []
        removed = False

        if not self.hosts_file.exists():
            print(f"❌ File {self.hosts_file} not found.", file=sys.stderr)
            return False

        try:
            with open(self.hosts_file, 'r') as f:
                raw_lines = f.readlines()

            for line in raw_lines:
                clean = line.strip()
                # Check active or commented entry
                # Remove both active and commented versions if they match
                is_commented = clean.startswith('#')
                parts = clean.lstrip('#').strip().split()

                # Handling inline comments for parts check
                real_parts = []
                for p in parts:
                    if p.startswith('#'): break
                    real_parts.append(p)

                if len(real_parts) >= 2 and self._is_valid_ip(real_parts[0]) and host in real_parts[1:]:
                    # Found matching line. We delete it entirely.
                    removed = True
                    continue # Skip writing this line

                lines.append(line)

            if removed:
                with open(self.hosts_file, 'w') as f:
                    f.writelines(lines)
                return True
            else:
                print(f"ℹ️  Host '{host}' not found.", file=sys.stderr)
                return False

        except PermissionError:
            print(f"❌ Permission denied writing to {self.hosts_file}. Try running with sudo.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ Error removing entry: {e}", file=sys.stderr)
            return False

    def toggle_entry(self, host: str) -> bool:
        """Toggles (comments/uncomments) an entry."""
        lines = []
        toggled = False
        target_state = None # True for enabled, False for disabled

        if not self.hosts_file.exists():
             print(f"❌ File {self.hosts_file} not found.", file=sys.stderr)
             return False

        try:
            with open(self.hosts_file, 'r') as f:
                raw_lines = f.readlines()

            for line in raw_lines:
                clean = line.strip()
                is_commented = clean.startswith('#')

                # Check contents
                content = clean.lstrip('#').strip()
                parts = content.split()

                real_parts = []
                for p in parts:
                    if p.startswith('#'): break
                    real_parts.append(p)

                if len(real_parts) >= 2 and self._is_valid_ip(real_parts[0]) and host in real_parts[1:]:
                    if is_commented:
                        # Enable
                        lines.append(f"{content}\n")
                        target_state = "enabled"
                    else:
                        # Disable
                        lines.append(f"# {line}")
                        target_state = "disabled"
                    toggled = True
                else:
                    lines.append(line)

            if toggled:
                with open(self.hosts_file, 'w') as f:
                    f.writelines(lines)
                print(f"✅ Host '{host}' is now {target_state}.")
                return True
            else:
                print(f"ℹ️  Host '{host}' not found.", file=sys.stderr)
                return False

        except PermissionError:
            print(f"❌ Permission denied writing to {self.hosts_file}. Try running with sudo.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ Error toggling entry: {e}", file=sys.stderr)
            return False

    def backup(self) -> Optional[Path]:
        """Creates a backup of the hosts file."""
        if not self.hosts_file.exists():
             print(f"❌ File {self.hosts_file} not found.", file=sys.stderr)
             return None

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.hosts_file.parent / f"{self.hosts_file.name}.bak.{ts}"
        try:
            shutil.copy2(self.hosts_file, dest)
            return dest
        except Exception as e:
            print(f"❌ Error creating backup: {e}", file=sys.stderr)
            return None

    def check_host(self, host: str) -> Dict[str, Any]:
        """Checks if the host resolves to the expected IP."""
        try:
            resolved_ip = socket.gethostbyname(host)
            return {"host": host, "ip": resolved_ip, "status": "ok"}
        except socket.error as e:
            return {"host": host, "error": str(e), "status": "error"}


def run_host_lab_logic(args):
    """CLI logic for Host Lab."""

    # Default path handling
    path_str = getattr(args, 'file', None)
    if not path_str:
        if sys.platform == "win32":
            path_str = r"C:\Windows\System32\drivers\etc\hosts"
        else:
            path_str = "/etc/hosts"

    hosts_path = Path(path_str)
    manager = HostLabManager(hosts_path)

    if args.action == "list":
        entries = manager.list_entries()
        print(f"--- Hosts in: {hosts_path} ---")
        if not entries:
            print("No entries found or empty file.")
            sys.exit(0)

        # Filter for active/managed entries first
        active = [e for e in entries if e['type'] == 'entry']

        if not active:
            print("No host entries found.")
        else:
            print(f"{'Status':<8} | {'IP':<15} | {'Host(s)':<30} | {'Comment'}")
            print("-" * 70)
            for e in active:
                status = "✅ ON" if e['enabled'] else "❌ OFF"
                hosts = ", ".join(e['hosts'])
                if len(hosts) > 30: hosts = hosts[:27] + "..."
                comment = e.get('comment', '') or ""
                print(f"{status:<8} | {e['ip']:<15} | {hosts:<30} | {comment}")
        sys.exit(0)

    elif args.action == "add":
        if not args.ip or not args.host:
            print("Error: --ip and --host are required for 'add'.", file=sys.stderr)
            sys.exit(1)

        if manager.add_entry(args.ip, args.host, args.comment):
            print(f"✅ Added {args.host} -> {args.ip}")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "remove":
        if not args.host:
             print("Error: --host is required for 'remove'.", file=sys.stderr)
             sys.exit(1)

        if manager.remove_entry(args.host):
            print(f"✅ Removed entry for {args.host}")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "toggle":
        if not args.host:
             print("Error: --host is required for 'toggle'.", file=sys.stderr)
             sys.exit(1)

        if manager.toggle_entry(args.host):
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "backup":
        backup_path = manager.backup()
        if backup_path:
            print(f"✅ Backup created at: {backup_path}")
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.action == "check":
        if not args.host:
             print("Error: --host is required for 'check'.", file=sys.stderr)
             sys.exit(1)

        result = manager.check_host(args.host)
        if result['status'] == 'ok':
            print(f"✅ {result['host']} resolves to {result['ip']}")

            # Check if this matches file
            entries = manager.list_entries()
            matching = [e for e in entries if e['type'] == 'entry' and args.host in e['hosts']]
            if matching:
                expected_ip = matching[0]['ip']
                if expected_ip == result['ip']:
                     print(f"   Matches config in {hosts_path}.")
                else:
                     print(f"⚠️  Mismatch! Config says {expected_ip}.")
            else:
                 print(f"ℹ️  Host not found in {hosts_path}.")

            sys.exit(0)
        else:
            print(f"❌ Resolution failed: {result.get('error')}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
