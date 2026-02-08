"""
Semantic Versioning Lab (semver-lab)
====================================

A CLI tool for parsing, validating, bumping, comparing, and sorting Semantic Versioning 2.0.0 strings.
"""

import re
import sys
import argparse
from typing import Optional, List, Union

# Official SemVer 2.0.0 regex
SEMVER_REGEX = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

class SemVer:
    def __init__(self, version_str: str):
        match = SEMVER_REGEX.match(version_str)
        if not match:
            raise ValueError(f"Invalid SemVer string: {version_str}")

        self.major = int(match.group("major"))
        self.minor = int(match.group("minor"))
        self.patch = int(match.group("patch"))
        self.prerelease = match.group("prerelease")
        self.buildmetadata = match.group("buildmetadata")
        self._raw = version_str

    def __str__(self):
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            s += f"-{self.prerelease}"
        if self.buildmetadata:
            s += f"+{self.buildmetadata}"
        return s

    def __repr__(self):
        return f"SemVer('{str(self)}')"

    def bump(self, part: str, pre_id: Optional[str] = None) -> 'SemVer':
        major, minor, patch = self.major, self.minor, self.patch
        prerelease = self.prerelease

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
            # If we are in a prerelease (e.g. 1.0.0-alpha), bumping patch means releasing 1.0.0
            # So we keep major.minor.patch as is, and remove prerelease.
            prerelease = None
        elif part == "prerelease":
            if prerelease:
                # Try to increment last number
                parts = prerelease.split('.')
                last = parts[-1]
                if last.isdigit():
                    parts[-1] = str(int(last) + 1)
                else:
                    parts.append("0")
                prerelease = ".".join(parts)
            else:
                # New prerelease from stable
                patch += 1
                prerelease = pre_id or "0"

        new_v_str = f"{major}.{minor}.{patch}"
        if prerelease:
            new_v_str += f"-{prerelease}"

        return SemVer(new_v_str)

    def compare(self, other: 'SemVer') -> int:
        # 1. Compare Major, Minor, Patch
        if self.major != other.major:
            return self.major - other.major
        if self.minor != other.minor:
            return self.minor - other.minor
        if self.patch != other.patch:
            return self.patch - other.patch

        # 2. Compare Prerelease
        # Pre-release versions have a lower precedence than the associated normal version.
        if self.prerelease and not other.prerelease:
            return -1
        if not self.prerelease and other.prerelease:
            return 1
        if not self.prerelease and not other.prerelease:
            return 0

        # Compare prerelease identifiers
        return self._compare_prerelease(self.prerelease, other.prerelease)

    def _compare_prerelease(self, pre1: str, pre2: str) -> int:
        parts1 = pre1.split('.')
        parts2 = pre2.split('.')

        for p1, p2 in zip(parts1, parts2):
            # Numeric identifiers are compared numerically
            if p1.isdigit() and p2.isdigit():
                i1, i2 = int(p1), int(p2)
                if i1 != i2:
                    return i1 - i2
            # Numeric identifiers always have lower precedence than non-numeric identifiers
            elif p1.isdigit() and not p2.isdigit():
                return -1
            elif not p1.isdigit() and p2.isdigit():
                return 1
            # Identifiers with letters or hyphens are compared lexically in ASCII sort order
            else:
                if p1 != p2:
                    return -1 if p1 < p2 else 1

        # A larger set of pre-release fields has a higher precedence than a smaller set
        return len(parts1) - len(parts2)

    def __lt__(self, other):
        return self.compare(other) < 0

    def __eq__(self, other):
        return self.compare(other) == 0

    def __le__(self, other):
        return self.compare(other) <= 0

    def __gt__(self, other):
        return self.compare(other) > 0

    def __ge__(self, other):
        return self.compare(other) >= 0

def run_semver_lab_logic(args):
    """
    Handles the CLI logic for semver-lab.
    """
    if args.action == "parse":
        try:
            v = SemVer(args.version)
            print(f"Original:       {v}")
            print(f"Major:          {v.major}")
            print(f"Minor:          {v.minor}")
            print(f"Patch:          {v.patch}")
            print(f"Prerelease:     {v.prerelease or '(none)'}")
            print(f"Build Metadata: {v.buildmetadata or '(none)'}")
            sys.exit(0)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "bump":
        try:
            v = SemVer(args.version)
            new_v = v.bump(args.part, args.pre_id)
            print(new_v)
            sys.exit(0)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "compare":
        try:
            v1 = SemVer(args.version1)
            v2 = SemVer(args.version2)
            if v1 < v2:
                print(f"{v1} < {v2}")
            elif v1 > v2:
                print(f"{v1} > {v2}")
            else:
                print(f"{v1} == {v2}")
            sys.exit(0)
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "sort":
        versions = []
        for v_str in args.versions:
            try:
                versions.append(SemVer(v_str))
            except ValueError:
                print(f"Warning: Skipping invalid version '{v_str}'", file=sys.stderr)

        sorted_versions = sorted(versions)
        if args.reverse:
            sorted_versions.reverse()

        for v in sorted_versions:
            print(v)
        sys.exit(0)

    elif args.action == "validate":
        try:
            SemVer(args.version)
            print(f"✅ Valid SemVer: {args.version}")
            sys.exit(0)
        except ValueError:
            print(f"❌ Invalid SemVer: {args.version}")
            sys.exit(1)
