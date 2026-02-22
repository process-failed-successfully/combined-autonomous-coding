import os
import sys
import stat
from pathlib import Path
from typing import Dict, Any, Tuple


class PermissionsManager:
    """Manager for Unix permissions operations."""

    def to_octal(self, r: bool, w: bool, x: bool) -> int:
        """Converts r, w, x booleans to a single octal digit (0-7)."""
        val = 0
        if r:
            val += 4
        if w:
            val += 2
        if x:
            val += 1
        return val

    def to_symbolic(self, r: bool, w: bool, x: bool) -> str:
        """Converts r, w, x booleans to a symbolic string (e.g., 'r-x')."""
        return "".join([
            "r" if r else "-",
            "w" if w else "-",
            "x" if x else "-"
        ])

    def from_octal(self, octal_digit: int) -> Tuple[bool, bool, bool]:
        """Converts an octal digit (0-7) to r, w, x booleans."""
        r = bool(octal_digit & 4)
        w = bool(octal_digit & 2)
        x = bool(octal_digit & 1)
        return r, w, x

    def calculate_mode(self, owner: int, group: int, other: int) -> int:
        """Calculates the full integer mode from owner, group, other octal digits."""
        # e.g., 7, 5, 5 -> 0o755
        return (owner * 64) + (group * 8) + other

    def get_permissions(self, path: str) -> Dict[str, Any]:
        """Gets permission details for a file path."""
        try:
            p = Path(path)
            if not p.exists():
                return {"error": "File not found"}

            st = p.stat()
            mode = st.st_mode

            # Extract octal digits
            # S_IRWXU = 0o700
            owner = (mode & stat.S_IRWXU) >> 6
            group = (mode & stat.S_IRWXG) >> 3
            other = (mode & stat.S_IRWXO)

            octal_str = f"{owner}{group}{other}"

            # Symbolic
            perms = stat.filemode(mode)
            # stat.filemode returns like '-rwxr-xr-x'
            # We want just the rwxr-xr-x part, usually 10 chars, first is type
            symbolic = perms[1:] if len(perms) > 1 else perms

            return {
                "path": str(p),
                "mode": mode,
                "octal": octal_str,
                "symbolic": symbolic,
                "owner_digit": owner,
                "group_digit": group,
                "other_digit": other
            }
        except Exception as e:
            return {"error": str(e)}

    def set_permissions(self, path: str, octal_str: str) -> bool:
        """Sets permissions for a file path using an octal string (e.g., '755')."""
        try:
            if not path:
                return False

            p = Path(path)
            if not p.exists():
                return False

            if not octal_str.isdigit() or len(octal_str) != 3:
                return False

            mode = int(octal_str, 8)
            os.chmod(p, mode)
            return True
        except Exception:
            return False

def run_permissions_lab_logic(args):
    """CLI logic for Permissions Lab."""
    manager = PermissionsManager()

    if args.action == "check":
        if not args.file:
            print("Error: --file argument is required for 'check'.", file=sys.stderr)
            sys.exit(1)

        result = manager.get_permissions(args.file)
        if "error" in result:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"File: {result['path']}")
        print(f"Octal: {result['octal']}")
        print(f"Symbolic: {result['symbolic']}")
        print(f"Owner: {result['owner_digit']}")
        print(f"Group: {result['group_digit']}")
        print(f"Other: {result['other_digit']}")
        sys.exit(0)

    elif args.action == "calc":
        if not args.value:
            print("Error: --value argument (octal or symbolic) is required for 'calc'.", file=sys.stderr)
            sys.exit(1)

        val = args.value

        # Determine if octal or symbolic
        if val.isdigit() and len(val) == 3:
            # Octal -> Symbolic
            try:
                owner = int(val[0])
                group = int(val[1])
                other = int(val[2])

                def get_sym(digit):
                    r, w, x = manager.from_octal(digit)
                    return manager.to_symbolic(r, w, x)

                sym = f"{get_sym(owner)}{get_sym(group)}{get_sym(other)}"
                print(f"Octal: {val}")
                print(f"Symbolic: {sym}")
                sys.exit(0)
            except Exception as e:
                print(f"❌ Error parsing octal: {e}", file=sys.stderr)
                sys.exit(1)
        elif len(val) == 9 and all(c in "rwx-" for c in val):
            # Symbolic -> Octal
            try:
                # rwxrwxrwx
                def get_oct(s):
                    r = s[0] == 'r'
                    w = s[1] == 'w'
                    x = s[2] == 'x'
                    return manager.to_octal(r, w, x)

                o1 = get_oct(val[0:3])
                o2 = get_oct(val[3:6])
                o3 = get_oct(val[6:9])

                octal = f"{o1}{o2}{o3}"
                print(f"Symbolic: {val}")
                print(f"Octal: {octal}")
                sys.exit(0)
            except Exception as e:
                print(f"❌ Error parsing symbolic: {e}", file=sys.stderr)
                sys.exit(1)
        else:
             print("Error: Invalid format. Use 3-digit octal (e.g., 755) or 9-char symbolic (e.g., rwxr-xr-x).", file=sys.stderr)
             sys.exit(1)

    elif args.action == "set":
        if not args.file or not args.value:
             print("Error: --file and --value (octal) are required for 'set'.", file=sys.stderr)
             sys.exit(1)

        if manager.set_permissions(args.file, args.value):
            print(f"✅ Permissions for '{args.file}' set to {args.value}.")
            sys.exit(0)
        else:
            print(f"❌ Failed to set permissions for '{args.file}'. Check if file exists and value is valid octal.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "explain":
        if not args.value:
            print("Error: --value argument (octal or symbolic) is required for 'explain'.", file=sys.stderr)
            sys.exit(1)

        val = args.value
        octal = ""
        symbolic = ""

        if val.isdigit() and len(val) == 3:
            octal = val
            try:
                o1, o2, o3 = int(val[0]), int(val[1]), int(val[2])
                s1 = manager.to_symbolic(*manager.from_octal(o1))
                s2 = manager.to_symbolic(*manager.from_octal(o2))
                s3 = manager.to_symbolic(*manager.from_octal(o3))
                symbolic = f"{s1}{s2}{s3}"
            except Exception:
                print("Error: Invalid octal string.", file=sys.stderr)
                sys.exit(1)
        elif len(val) == 9:
            symbolic = val
            try:
                def get_oct(s):
                    return manager.to_octal(s[0]=='r', s[1]=='w', s[2]=='x')
                o1 = get_oct(val[0:3])
                o2 = get_oct(val[3:6])
                o3 = get_oct(val[6:9])
                octal = f"{o1}{o2}{o3}"
            except Exception:
                print("Error: Invalid symbolic string.", file=sys.stderr)
                sys.exit(1)
        else:
            print("Error: Invalid format.", file=sys.stderr)
            sys.exit(1)

        print(f"Octal: {octal}")
        print(f"Symbolic: {symbolic}\n")

        def describe(perm_str):
            parts = []
            if perm_str[0] == 'r': parts.append("Read")
            if perm_str[1] == 'w': parts.append("Write")
            if perm_str[2] == 'x': parts.append("Execute")
            if not parts: return "None"
            return ", ".join(parts)

        print(f"Owner: {describe(symbolic[0:3])}")
        print(f"Group: {describe(symbolic[3:6])}")
        print(f"Other: {describe(symbolic[6:9])}")
        sys.exit(0)

    sys.exit(0)
