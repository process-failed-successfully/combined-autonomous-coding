import os
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
