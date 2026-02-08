import re
import sys
from typing import Optional, Tuple, List, Union

class SemVer:
    """
    Represents a Semantic Version (SemVer 2.0.0).
    """
    # Regex for SemVer 2.0.0 from semver.org
    REGEX = re.compile(
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )

    def __init__(self, major: int, minor: int, patch: int, prerelease: Optional[str] = None, build: Optional[str] = None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease
        self.build = build

    @classmethod
    def parse(cls, version_str: str) -> 'SemVer':
        """Parses a version string into a SemVer object."""
        match = cls.REGEX.match(version_str.strip())
        if not match:
            raise ValueError(f"Invalid SemVer string: {version_str}")

        data = match.groupdict()
        return cls(
            major=int(data['major']),
            minor=int(data['minor']),
            patch=int(data['patch']),
            prerelease=data['prerelease'],
            build=data['build']
        )

    def bump(self, part: str, pre_id: str = "alpha") -> 'SemVer':
        """Bumps the specified part of the version."""
        major, minor, patch = self.major, self.minor, self.patch
        prerelease, build = self.prerelease, None # Build is cleared on bump usually

        if part == "major":
            major += 1
            minor = 0
            patch = 0
            prerelease = None
        elif part == "minor":
            minor += 1
            patch = 0
            prerelease = None
        elif part == "patch":
            if not prerelease:
                patch += 1
            else:
                # If bumping patch of a pre-release, we just clear pre-release to "release" it?
                # Or do we increment patch?
                # Standard behavior: 1.0.0-alpha -> 1.0.0 (release) -> 1.0.1 (patch)
                # But if we ask to bump patch on 1.0.0-alpha, typically it means 1.0.0.
                # However, most tools treat 'patch' as incrementing the patch number.
                # If we are pre-release, we usually want to stabilize to release first.
                # Let's follow semver behavior:
                # If we have a prerelease, and we bump patch, we clear prerelease (release it).
                # 1.2.3-alpha.1 bump patch -> 1.2.3
                # Wait, usually 1.2.3-alpha.1 bump patch -> 1.2.3 (release) is 'release' action.
                # If I strictly bump patch: 1.2.3-alpha.1 -> 1.2.4 ? No.
                # Let's assume standard "npm version patch" behavior.
                # 1.2.3-alpha.1 -> 1.2.3 (it strips prerelease if the base is what we want)
                # Actually, npm version patch on 1.2.3-alpha.1 -> 1.2.3 is NOT what happens.
                # npm version patch on 1.0.0-0 -> 1.0.0
                # Let's simplify:
                # major/minor/patch bumps reset prerelease.
                # If strictly bumping number:
                patch += 1
                prerelease = None
        elif part == "prerelease":
            # If already prerelease, increment last number or append .0
            if prerelease:
                prerelease = self._increment_prerelease(prerelease)
            else:
                # Start new prerelease on next patch
                patch += 1
                prerelease = f"{pre_id}.0"
        elif part == "premajor":
            major += 1
            minor = 0
            patch = 0
            prerelease = f"{pre_id}.0"
        elif part == "preminor":
            minor += 1
            patch = 0
            prerelease = f"{pre_id}.0"
        elif part == "prepatch":
            patch += 1
            prerelease = f"{pre_id}.0"
        else:
            raise ValueError(f"Unknown bump part: {part}")

        return SemVer(major, minor, patch, prerelease, build)

    def _increment_prerelease(self, pre: str) -> str:
        parts = pre.split('.')
        # Look for the last numeric part
        for i in range(len(parts) - 1, -1, -1):
            if parts[i].isdigit():
                parts[i] = str(int(parts[i]) + 1)
                return ".".join(parts)
        # If no numeric part, append .0
        return pre + ".0"

    def __str__(self):
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            s += f"-{self.prerelease}"
        if self.build:
            s += f"+{self.build}"
        return s

    def __repr__(self):
        return f"SemVer('{self}')"

    def __eq__(self, other):
        if not isinstance(other, SemVer):
            return False
        return self.compare(other) == 0

    def __lt__(self, other):
        if not isinstance(other, SemVer):
            raise TypeError("Cannot compare SemVer with non-SemVer")
        return self.compare(other) < 0

    def __gt__(self, other):
        return other < self

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def compare(self, other: 'SemVer') -> int:
        """
        Returns -1 if self < other, 0 if equal, 1 if self > other.
        Precedence ignores build metadata.
        """
        if self.major != other.major:
            return 1 if self.major > other.major else -1
        if self.minor != other.minor:
            return 1 if self.minor > other.minor else -1
        if self.patch != other.patch:
            return 1 if self.patch > other.patch else -1

        # Check pre-release
        # Pre-release version has lower precedence than normal version
        if self.prerelease and not other.prerelease:
            return -1
        if not self.prerelease and other.prerelease:
            return 1
        if not self.prerelease and not other.prerelease:
            return 0

        # Both have pre-release, compare identifiers
        return self._compare_prerelease(self.prerelease, other.prerelease)

    def _compare_prerelease(self, pre1: str, pre2: str) -> int:
        parts1 = pre1.split('.')
        parts2 = pre2.split('.')

        for i in range(min(len(parts1), len(parts2))):
            p1 = parts1[i]
            p2 = parts2[i]

            p1_is_num = p1.isdigit()
            p2_is_num = p2.isdigit()

            if p1_is_num and p2_is_num:
                i1, i2 = int(p1), int(p2)
                if i1 != i2:
                    return 1 if i1 > i2 else -1
            elif not p1_is_num and not p2_is_num:
                if p1 != p2:
                    return 1 if p1 > p2 else -1
            else:
                # Numeric identifiers always have lower precedence than non-numeric identifiers
                # Wait, spec says: "Numeric identifiers always have lower precedence than non-numeric identifiers."
                if p1_is_num: # p1 is num, p2 is str -> p1 < p2
                    return -1
                else: # p1 is str, p2 is num -> p1 > p2
                    return 1

        # If all equal so far, larger set of fields has higher precedence
        if len(parts1) != len(parts2):
            return 1 if len(parts1) > len(parts2) else -1

        return 0

class SemVerLabManager:
    """CLI logic for SemVer Lab."""

    def parse(self, version: str) -> dict:
        try:
            v = SemVer.parse(version)
            return {
                "valid": True,
                "version": str(v),
                "major": v.major,
                "minor": v.minor,
                "patch": v.patch,
                "prerelease": v.prerelease,
                "build": v.build
            }
        except ValueError as e:
            return {"valid": False, "error": str(e)}

    def bump(self, version: str, part: str, pre_id: str = "alpha") -> str:
        v = SemVer.parse(version)
        return str(v.bump(part, pre_id))

    def compare(self, v1_str: str, operator: str, v2_str: str) -> bool:
        v1 = SemVer.parse(v1_str)
        v2 = SemVer.parse(v2_str)

        if operator == "==" or operator == "eq":
            return v1 == v2
        elif operator == ">" or operator == "gt":
            return v1 > v2
        elif operator == "<" or operator == "lt":
            return v1 < v2
        elif operator == ">=" or operator == "ge":
            return v1 >= v2
        elif operator == "<=" or operator == "le":
            return v1 <= v2
        elif operator == "!=" or operator == "ne":
            return not (v1 == v2)
        else:
            raise ValueError(f"Unknown operator: {operator}")

    def sort(self, versions: List[str]) -> List[str]:
        valid_versions = []
        for v in versions:
            try:
                valid_versions.append(SemVer.parse(v))
            except ValueError:
                pass # Ignore invalid

        valid_versions.sort()
        return [str(v) for v in valid_versions]

def run_semver_lab_logic(args):
    manager = SemVerLabManager()

    if args.action == "parse":
        result = manager.parse(args.version)
        if result["valid"]:
            print(f"✅ Valid SemVer: {result['version']}")
            print(f"  Major: {result['major']}")
            print(f"  Minor: {result['minor']}")
            print(f"  Patch: {result['patch']}")
            print(f"  Pre-release: {result['prerelease']}")
            print(f"  Build: {result['build']}")
        else:
            print(f"❌ Invalid SemVer: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "bump":
        try:
            new_ver = manager.bump(args.version, args.part, args.pre_id)
            print(new_ver)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "compare":
        try:
            res = manager.compare(args.v1, args.operator, args.v2)
            print("true" if res else "false")
            sys.exit(0 if res else 1)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(2)

    elif args.action == "sort":
        # Read versions from stdin or args
        versions = args.versions
        if not versions and not sys.stdin.isatty():
             versions = sys.stdin.read().split()

        if not versions:
            print("Error: No versions provided.", file=sys.stderr)
            sys.exit(1)

        sorted_versions = manager.sort(versions)
        for v in sorted_versions:
            print(v)

    elif args.action == "satisfies":
        # Basic range implementation for CLI convenience
        # Supports >, <, >=, <=, =
        # e.g. satisfies 1.2.3 ">=1.0.0"
        # We can reuse compare logic if the range is simple
        version = args.version
        range_str = args.range

        # Simple parsing for single operator ranges
        match = re.match(r"^([<>]=?|==?|!=)\s*(.*)$", range_str.strip())
        if match:
            op, target = match.groups()
            try:
                res = manager.compare(version, op, target)
                print("true" if res else "false")
                sys.exit(0 if res else 1)
            except ValueError as e:
                print(f"❌ Error: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print("❌ Complex ranges (e.g. ^1.2.3 or 1.x) are not yet supported in this basic lab.", file=sys.stderr)
            print("   Supported: >, <, >=, <=, ==, !=", file=sys.stderr)
            sys.exit(1)
