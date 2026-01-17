"""
Security Utilities
==================

Provides security auditing capabilities, including static analysis (via bandit)
and secret scanning.
"""

import json
import logging
import re
import shutil
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SecurityAuditor:
    """
    Audits a project for security vulnerabilities using static analysis
    and pattern matching for secrets.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.bandit_path = shutil.which("bandit")

    def run_bandit(self, severity: str = "low", confidence: str = "low") -> Dict[str, Any]:
        """
        Runs bandit static analysis on the project.

        Args:
            severity: Minimum severity to report ('low', 'medium', 'high').
            confidence: Minimum confidence to report ('low', 'medium', 'high').

        Returns:
            A dictionary containing the bandit report.
        """
        if not self.bandit_path:
            return {"error": "Bandit tool not found. Please install it (pip install bandit)."}

        logger.info(f"Running bandit on {self.project_dir}")

        # Map simple severity/confidence strings to bandit flags if needed,
        # but bandit accepts -l, -ll, -lll.
        # Actually, modern bandit supports --severity-level {low,medium,high}
        # and --confidence-level {low,medium,high}

        cmd = [
            self.bandit_path,
            "-r", str(self.project_dir),
            "-f", "json",
            "--severity-level", severity.lower(),
            "--confidence-level", confidence.lower(),
            "--exclude", "/.venv,/.git,/node_modules,/__pycache__"
        ]

        try:
            # Bandit returns exit code 1 if issues are found, so we don't check=True
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse bandit output", "raw_output": result.stdout}
            else:
                 # If no output (unlikely with json format unless error), check stderr
                 return {"error": "Bandit produced no output", "stderr": result.stderr}

        except Exception as e:
            return {"error": f"Error running bandit: {e}"}

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """
        Scans the project for potential secrets (keys, tokens) using regex patterns.
        Respects .gitignore by using git ls-files if available.
        """
        logger.info(f"Scanning for secrets in {self.project_dir}")

        findings = []

        # Define patterns for common secrets
        patterns = {
            "AWS Access Key": r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
            "AWS Secret Key": r"(?i)aws_secret_access_key.{0,20}=.{0,20}([a-zA-Z0-9\/+]{40})",
            "Generic API Key": r"(?i)(api_key|apikey|secret_key|auth_token|access_token).{0,20}['\"]([a-zA-Z0-9_\-]{16,})['\"]",
            "Private Key": r"-----BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----",
            "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})",
            "Stripe Key": r"(sk_live_|pk_live_)[0-9a-zA-Z]{24}",
        }

        files_to_scan = self._get_files_to_scan()

        for file_path in files_to_scan:
            try:
                # Read file safely, skip binaries
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                for name, pattern in patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # Get line number
                        line_num = content.count("\n", 0, match.start()) + 1

                        # Get context (snippet)
                        start = max(0, match.start() - 20)
                        end = min(len(content), match.end() + 20)
                        snippet = content[start:end].replace("\n", " ")

                        findings.append({
                            "type": name,
                            "file": str(file_path.relative_to(self.project_dir)),
                            "line": line_num,
                            "snippet": snippet # Be careful showing this in logs!
                        })
            except Exception as e:
                logger.warning(f"Error scanning file {file_path}: {e}")

        return findings

    def _get_files_to_scan(self) -> List[Path]:
        """
        Returns a list of files to scan, preferring git ls-files.
        """
        files = []

        # Try git ls-files first
        git_path = shutil.which("git")
        if git_path and (self.project_dir / ".git").is_dir():
            try:
                result = subprocess.run(
                    [git_path, "-C", str(self.project_dir), "ls-files"],
                    capture_output=True, text=True, check=True
                )
                for line in result.stdout.splitlines():
                    full_path = self.project_dir / line
                    if full_path.is_file():
                        files.append(full_path)
                return files
            except subprocess.CalledProcessError:
                logger.warning("git ls-files failed, falling back to os.walk")

        # Fallback to os.walk
        ignored_dirs = {".git", ".venv", "node_modules", "__pycache__", ".idea", ".vscode", "venv", "env"}

        for root, dirs, filenames in os.walk(self.project_dir):
            # Prune ignored dirs
            dirs[:] = [d for d in dirs if d not in ignored_dirs]

            for filename in filenames:
                file_path = Path(root) / filename
                # Skip large files or known binary extensions could be added here
                if file_path.suffix.lower() not in ['.pyc', '.so', '.dll', '.exe', '.bin', '.png', '.jpg']:
                     files.append(file_path)

        return files

    def audit(self, scan_type: str = "all", severity: str = "low") -> Dict[str, Any]:
        """
        Runs the specified checks and aggregates results.
        """
        results = {
            "bandit": None,
            "secrets": None,
            "summary": {"total_issues": 0}
        }

        if scan_type in ["all", "bandit"]:
            bandit_report = self.run_bandit(severity=severity)
            results["bandit"] = bandit_report

            # Count bandit issues
            if "results" in bandit_report:
                results["summary"]["total_issues"] += len(bandit_report["results"])

        if scan_type in ["all", "secrets"]:
            secrets = self.scan_secrets()
            results["secrets"] = secrets
            results["summary"]["total_issues"] += len(secrets)

        return results
