import os
import sys
from pathlib import Path
from typing import Dict, Any, List

try:
    import pwd
    import grp
    HAVE_PWD = True
except ImportError:
    HAVE_PWD = False


class ChownManager:
    """Manager for Unix ownership operations."""

    def __init__(self):
        self.have_pwd = HAVE_PWD

    def get_user_name(self, uid: int) -> str:
        """Returns the username for a given UID."""
        if not self.have_pwd:
            return str(uid)
        try:
            return pwd.getpwuid(uid).pw_name
        except KeyError:
            return str(uid)

    def get_group_name(self, gid: int) -> str:
        """Returns the group name for a given GID."""
        if not self.have_pwd:
            return str(gid)
        try:
            return grp.getgrgid(gid).gr_name
        except KeyError:
            return str(gid)

    def get_uid(self, user_str: str) -> int:
        """Returns the UID for a username or numeric string."""
        if user_str.isdigit():
            return int(user_str)
        if not self.have_pwd:
            raise ValueError(f"pwd module unavailable. Cannot resolve user '{user_str}'")
        try:
            return pwd.getpwnam(user_str).pw_uid
        except KeyError:
            raise ValueError(f"User '{user_str}' not found")

    def get_gid(self, group_str: str) -> int:
        """Returns the GID for a group name or numeric string."""
        if group_str.isdigit():
            return int(group_str)
        if not self.have_pwd:
            raise ValueError(f"grp module unavailable. Cannot resolve group '{group_str}'")
        try:
            return grp.getgrnam(group_str).gr_gid
        except KeyError:
            raise ValueError(f"Group '{group_str}' not found")

    def get_ownership(self, path: str) -> Dict[str, Any]:
        """Gets ownership details for a file path."""
        try:
            p = Path(path)
            if not p.exists():
                return {"error": "File not found"}

            st = p.stat()
            uid = st.st_uid
            gid = st.st_gid

            user = self.get_user_name(uid)
            group = self.get_group_name(gid)

            return {
                "path": str(p),
                "uid": uid,
                "gid": gid,
                "user": user,
                "group": group,
                "formatted": f"{user}:{group}"
            }
        except Exception as e:
            return {"error": str(e)}

    def set_ownership(self, path: str, owner_str: str) -> bool:
        """Sets ownership using format user:group, user, or :group."""
        try:
            p = Path(path)
            if not p.exists():
                return False

            user_part = ""
            group_part = ""

            if ":" in owner_str:
                parts = owner_str.split(":", 1)
                user_part = parts[0].strip()
                group_part = parts[1].strip()
            else:
                user_part = owner_str.strip()

            uid = -1
            gid = -1

            if user_part:
                uid = self.get_uid(user_part)
            if group_part:
                gid = self.get_gid(group_part)

            os.chown(p, uid, gid)
            return True
        except Exception:
            return False

    def list_users(self) -> List[Dict[str, Any]]:
        """Returns a list of all system users."""
        if not self.have_pwd:
            return []
        users = []
        for p in pwd.getpwall():
            users.append({"user": p.pw_name, "uid": p.pw_uid, "dir": p.pw_dir, "shell": p.pw_shell})
        return sorted(users, key=lambda x: x["uid"])

    def list_groups(self) -> List[Dict[str, Any]]:
        """Returns a list of all system groups."""
        if not self.have_pwd:
            return []
        groups = []
        for g in grp.getgrall():
            groups.append({"group": g.gr_name, "gid": g.gr_gid, "members": g.gr_mem})
        return sorted(groups, key=lambda x: x["gid"])


def run_chown_lab_logic(args):
    """CLI logic for Chown Lab."""
    manager = ChownManager()

    if args.action == "check":
        if not args.file:
            print("Error: --file argument is required for 'check'.", file=sys.stderr)
            sys.exit(1)

        result = manager.get_ownership(args.file)
        if "error" in result:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"File: {result['path']}")
        print(f"User: {result['user']} (UID: {result['uid']})")
        print(f"Group: {result['group']} (GID: {result['gid']})")
        print(f"Ownership: {result['formatted']}")
        sys.exit(0)

    elif args.action == "set":
        if not args.file or not args.value:
            print("Error: --file and --value are required for 'set'.", file=sys.stderr)
            sys.exit(1)

        if manager.set_ownership(args.file, args.value):
            print(f"✅ Ownership for '{args.file}' set to {args.value}.")
            sys.exit(0)
        else:
            print(f"❌ Failed to set ownership for '{args.file}'. Check if file exists, user/group are valid, and you have sufficient permissions.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "list":
        if args.type == "users":
            users = manager.list_users()
            if not users:
                print("No users found or pwd module unavailable.")
                sys.exit(0)
            print(f"{'UID':<10} {'User':<20} {'Home':<30} {'Shell'}")
            print("-" * 75)
            for u in users:
                print(f"{u['uid']:<10} {u['user']:<20} {u['dir']:<30} {u['shell']}")
        elif args.type == "groups":
            groups = manager.list_groups()
            if not groups:
                print("No groups found or grp module unavailable.")
                sys.exit(0)
            print(f"{'GID':<10} {'Group':<20} {'Members'}")
            print("-" * 50)
            for g in groups:
                members = ",".join(g['members'])
                print(f"{g['gid']:<10} {g['group']:<20} {members}")
        else:
             print("Error: Invalid type. Use 'users' or 'groups'.", file=sys.stderr)
             sys.exit(1)
        sys.exit(0)

    sys.exit(0)
