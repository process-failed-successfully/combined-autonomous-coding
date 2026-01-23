"""
Release Management Utilities
============================

Functions for automating the release process: version bumping, changelog generation, and tagging.
"""

import shutil
import subprocess
import re
import json
import os
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from datetime import datetime

# Regex for Semantic Versioning
SEMVER_REGEX = r"v?(\d+)\.(\d+)\.(\d+)"

def get_latest_tag(project_dir: Path) -> Optional[str]:
    """Returns the latest git tag (reachable from HEAD)."""
    git_path = shutil.which("git")
    if not git_path:
        return None

    try:
        # Get the latest tag reachable from the current commit
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except subprocess.CalledProcessError:
        pass

    return None

def get_commits_since_tag(project_dir: Path, tag: Optional[str]) -> List[Dict[str, str]]:
    """Returns a list of commits since the given tag (or all commits if no tag)."""
    git_path = shutil.which("git")
    if not git_path:
        return []

    range_spec = f"{tag}..HEAD" if tag else "HEAD"

    try:
        # Format: Hash|Subject|Body
        # We use a separator that is unlikely to be in the message
        sep = "|||"
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "log", f"--format=%H{sep}%s{sep}%b", range_spec],
            capture_output=True, text=True, check=True
        )

        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split(sep)
            if len(parts) >= 2:
                commit_hash = parts[0]
                subject = parts[1]
                body = parts[2] if len(parts) > 2 else ""
                commits.append({
                    "hash": commit_hash,
                    "subject": subject,
                    "body": body
                })
        return commits
    except subprocess.CalledProcessError:
        return []

def determine_next_version(current_version_str: Optional[str], commits: List[Dict[str, str]]) -> str:
    """
    Determines the next semantic version based on commit messages.
    If current_version_str is None, returns "0.1.0".
    """
    if not current_version_str:
        return "0.1.0"

    # Parse current version
    match = re.match(SEMVER_REGEX, current_version_str)
    if not match:
        # Fallback if we can't parse the current version, maybe just append .1?
        # But let's assume standard semver for now.
        return current_version_str + ".1"

    major, minor, patch = map(int, match.groups())

    bump_type = None # None, 'patch', 'minor', 'major'

    for commit in commits:
        subject = commit['subject']
        body = commit['body']

        # Check for BREAKING CHANGE
        if "BREAKING CHANGE" in body or "BREAKING CHANGE" in subject:
            bump_type = "major"
            break # Max bump found

        # Check for types
        # Conventional commits: type(scope): description
        # We allow simplified: type: description

        # Check for minor bump (feat)
        if re.match(r"feat(\(.*\))?!?:", subject):
            if bump_type != "major":
                bump_type = "minor"

        # Check for patch bump (fix)
        elif re.match(r"fix(\(.*\))?!?:", subject):
            if bump_type is None:
                bump_type = "patch"

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    # else: no bump, return current

    return f"{major}.{minor}.{patch}"

def generate_changelog(commits: List[Dict[str, str]], new_version: str) -> str:
    """Generates a simple Markdown changelog from commits."""

    features = []
    fixes = []
    others = []
    breaking = []

    for commit in commits:
        subject = commit['subject']
        body = commit['body']
        commit_hash = commit['hash'][:7]
        line = f"- {subject} ({commit_hash})"

        if "BREAKING CHANGE" in body or "BREAKING CHANGE" in subject:
            breaking.append(line)

        if re.match(r"feat(\(.*\))?!?:", subject):
            features.append(line)
        elif re.match(r"fix(\(.*\))?!?:", subject):
            fixes.append(line)
        else:
            others.append(line)

    date_str = datetime.now().strftime("%Y-%m-%d")
    changelog = [f"# v{new_version} ({date_str})"]

    if breaking:
        changelog.append("\n## ⚠ BREAKING CHANGES")
        changelog.extend(breaking)

    if features:
        changelog.append("\n## Features")
        changelog.extend(features)

    if fixes:
        changelog.append("\n## Bug Fixes")
        changelog.extend(fixes)

    if others:
        changelog.append("\n## Other Changes")
        changelog.extend(others)

    return "\n".join(changelog)

def bump_version_file(project_dir: Path, new_version: str, dry_run: bool = False) -> List[str]:
    """
    Updates version in package.json or pyproject.toml.
    Returns a list of modified files.
    """
    modified_files = []

    # 1. package.json
    pkg_json = project_dir / "package.json"
    if pkg_json.exists():
        try:
            content = json.loads(pkg_json.read_text())
            content['version'] = new_version
            if not dry_run:
                pkg_json.write_text(json.dumps(content, indent=2) + "\n")
            modified_files.append("package.json")
        except Exception:
            pass # Ignore errors

    # 2. pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            text = pyproject.read_text()
            # Regex to find version = "..." in [tool.poetry] or [project]
            # Simple replacement for the first occurrence of version = "..."
            # This is a bit naive but standard for a simple tool without toml deps
            new_text = re.sub(r'(^version\s*=\s*")([^"]+)(")', f'\\g<1>{new_version}\\g<3>', text, count=1, flags=re.MULTILINE)
            if text != new_text:
                if not dry_run:
                    pyproject.write_text(new_text)
                modified_files.append("pyproject.toml")
        except Exception:
            pass

    return modified_files

def parse_current_version(project_dir: Path) -> Optional[str]:
    """Attempts to read the current version from config files."""
    # 1. package.json
    pkg_json = project_dir / "package.json"
    if pkg_json.exists():
        try:
            content = json.loads(pkg_json.read_text())
            if 'version' in content:
                return content['version']
        except Exception:
            pass

    # 2. pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            text = pyproject.read_text()
            match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
            if match:
                return match.group(1)
        except Exception:
            pass

    return None

def perform_release(project_dir: Path, new_version: str, changelog: str, dry_run: bool = False) -> Tuple[bool, str]:
    """
    Executes the release process:
    1. Bumps version in files.
    2. Commits changes.
    3. Creates a git tag using the changelog as the message.
    """
    git_path = shutil.which("git")
    if not git_path:
        return False, "Git executable not found."

    if dry_run:
        return True, f"[Dry Run] Would release v{new_version}."

    # 1. Bump files
    modified_files = bump_version_file(project_dir, new_version)

    # 2. Commit
    if modified_files:
        try:
            subprocess.run([git_path, "-C", str(project_dir), "add"] + modified_files, check=True, capture_output=True)
            subprocess.run([git_path, "-C", str(project_dir), "commit", "-m", f"chore: bump version to {new_version}"], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            return False, f"Git commit failed: {e}"

    # 3. Create Tag
    tag_name = f"v{new_version}"
    try:
        # Use a temporary file for the tag message to avoid shell escaping issues
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
            tf.write(changelog)
            tf_path = tf.name

        try:
            subprocess.run([git_path, "-C", str(project_dir), "tag", "-a", tag_name, "-F", tf_path], check=True, capture_output=True)
        finally:
            os.unlink(tf_path)

        return True, f"Release {tag_name} created successfully."
    except subprocess.CalledProcessError as e:
        # Attempt to rollback commit if tag fails?
        # For simplicity, we just report error. The commit remains.
        return False, f"Git tag failed: {e}"
