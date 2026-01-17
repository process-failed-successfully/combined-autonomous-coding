import os
import subprocess
import re
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

class SecurityAuditor:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def run_bandit(self, severity: str = "medium") -> Dict[str, Any]:
        """Runs bandit security linter on the project."""
        if not shutil.which("bandit"):
            return {"error": "Bandit is not installed. Please install it with 'pip install bandit'."}

        # bandit -r . -f json --severity-level (severity)
        cmd = ["bandit", "-r", str(self.project_dir), "-f", "json", "--severity-level", severity.lower()]

        try:
            # Explicitly capture stdout/stderr to avoid leaking to console
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Bandit returns exit code 1 if issues are found, which is fine.

            output = result.stdout.strip()
            if not output:
                 # Check stderr if stdout is empty
                 return {"error": "Bandit produced no output.", "stderr": result.stderr}

            try:
                data = json.loads(output)
                return data
            except json.JSONDecodeError:
                return {"error": "Failed to parse bandit output", "raw_output": output}
        except Exception as e:
            return {"error": str(e)}

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """Scans for potential secrets/keys in the codebase."""
        patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "Generic Private Key": r"-----BEGIN PRIVATE KEY-----",
            "GitHub Token": r"ghp_[A-Za-z0-9]{36}",
            "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
            "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})",
        }

        findings = []

        # Use git ls-files if available to respect .gitignore
        git_path = shutil.which("git")
        files_to_scan = []

        if git_path and (self.project_dir / ".git").exists():
            try:
                # Use --full-name to get paths relative to repo root, but we need absolute paths
                # Actually subprocess cwd handles it
                result = subprocess.run(
                    [git_path, "-C", str(self.project_dir), "ls-files"],
                    capture_output=True, text=True, check=True
                )
                # git ls-files returns relative paths
                files_to_scan = [self.project_dir / f for f in result.stdout.splitlines()]
            except subprocess.CalledProcessError:
                pass

        if not files_to_scan:
            # Fallback to os.walk
            for root, dirs, files in os.walk(self.project_dir):
                # Skip common ignored dirs
                if ".git" in dirs: dirs.remove(".git")
                if ".venv" in dirs: dirs.remove(".venv")
                if "node_modules" in dirs: dirs.remove("node_modules")
                if "__pycache__" in dirs: dirs.remove("__pycache__")
                if ".agent_trash" in dirs: dirs.remove(".agent_trash")
                if ".agent_archives" in dirs: dirs.remove(".agent_archives")

                for file in files:
                    files_to_scan.append(Path(root) / file)

        for file_path in files_to_scan:
            if not file_path.is_file(): continue

            # Skip binary files/images based on extension (heuristic)
            if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.pyc', '.db', '.sqlite']:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for name, pattern in patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_no = content[:match.start()].count('\n') + 1
                        match_text = match.group(0)
                        # Redact for display
                        redacted = match_text[:4] + "..." + match_text[-4:] if len(match_text) > 8 else "***"

                        findings.append({
                            "type": name,
                            "file": str(file_path.relative_to(self.project_dir)),
                            "line": line_no,
                            "match": redacted
                        })
            except Exception:
                continue

        return findings

    def audit(self, scan_type: str = "all", severity: str = "medium") -> Dict[str, Any]:
        """Runs the specified audits and returns a consolidated report."""
        report = {}

        if scan_type in ["all", "bandit"]:
            report["bandit"] = self.run_bandit(severity)

        if scan_type in ["all", "secrets"]:
            report["secrets"] = self.scan_secrets()

        return report
