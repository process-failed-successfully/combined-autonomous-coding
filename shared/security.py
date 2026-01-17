"""
Security Utilities
==================

Shared utilities for running security scans (bandit, secret scanning).
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class SecurityAuditor:
    """Handles security scanning operations."""

    def __init__(self, project_dir: Path, severity: str = "MEDIUM"):
        self.project_dir = project_dir
        self.severity = severity.upper()  # LOW, MEDIUM, HIGH
        self.results: Dict[str, Any] = {
            "bandit": {},
            "secrets": [],
            "summary": {}
        }

    async def run_all(self):
        """Runs all configured security checks."""
        await self.run_bandit()
        self.scan_secrets()
        self._generate_summary()

    async def run_bandit(self):
        """Runs Bandit SAST scan."""
        bandit_path = shutil.which("bandit")
        if not bandit_path:
            logger.warning("Bandit not found. Skipping SAST scan.")
            self.results["bandit"] = {"error": "Bandit tool not installed."}
            return

        severity_flag = "-ll" if self.severity == "MEDIUM" else "-lll" if self.severity == "HIGH" else "-l"

        # Construct command
        cmd = [
            bandit_path,
            "-r", str(self.project_dir),
            "-f", "json",
            severity_flag,
            "--exclude", ".venv,venv,tests,.git,__pycache__",
            "--quiet"  # Suppress progress bar
        ]

        logger.info(f"Running Bandit: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            # Bandit returns non-zero exit code if issues are found, which is fine.
            # We just want the JSON output.
            output_str = stdout.decode()
            if output_str.strip():
                try:
                    # Bandit output might contain other text if not completely quiet, try to find JSON start
                    if output_str.strip().startswith("{"):
                        self.results["bandit"] = json.loads(output_str)
                    else:
                        # Attempt to find the start of the JSON block
                        start_idx = output_str.find("{")
                        if start_idx != -1:
                            self.results["bandit"] = json.loads(output_str[start_idx:])
                        else:
                             self.results["bandit"] = {"error": "Failed to parse Bandit JSON output", "raw": output_str}
                except json.JSONDecodeError:
                    self.results["bandit"] = {"error": "Failed to parse Bandit JSON output", "raw": output_str}
            else:
                 self.results["bandit"] = {"results": []}

        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")
            self.results["bandit"] = {"error": str(e)}

    def scan_secrets(self):
        """Scans for potential secrets (API keys, tokens) using regex."""
        logger.info("Scanning for secrets...")

        # Common patterns for secrets
        patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "Generic Private Key": r"-----BEGIN PRIVATE KEY-----",
            "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})?",
            "GitHub Token": r"gh[pousr]_[A-Za-z0-9_]{36,255}",
            "Google API Key": r"AIza[0-9A-Za-z\\-_]{35}",
        }

        found_secrets = []

        # Use git grep if available for speed and respecting .gitignore
        # Fallback to os.walk
        use_git = (self.project_dir / ".git").is_dir() and shutil.which("git")

        for name, pattern in patterns.items():
            try:
                if use_git:
                    # git grep -n "pattern"
                    cmd = ["git", "grep", "-n", "-E", pattern]
                    result = subprocess.run(
                        cmd, cwd=self.project_dir, capture_output=True, text=True
                    )
                    if result.returncode == 0 and result.stdout:
                        for line in result.stdout.splitlines():
                            found_secrets.append(f"[{name}] {line.strip()}")
                else:
                    # Fallback walk
                    regex = re.compile(pattern)
                    for root, _, files in os.walk(self.project_dir):
                        if ".git" in root or ".venv" in root or "__pycache__" in root:
                            continue
                        for file in files:
                            path = Path(root) / file
                            try:
                                with open(path, "r", errors="ignore") as f:
                                    for i, line in enumerate(f, 1):
                                        if regex.search(line):
                                            rel_path = path.relative_to(self.project_dir)
                                            found_secrets.append(f"[{name}] {rel_path}:{i}: {line.strip()[:50]}...")
                            except Exception:
                                pass # Skip binary or unreadable files
            except Exception as e:
                logger.warning(f"Error scanning for {name}: {e}")

        self.results["secrets"] = found_secrets

    def _generate_summary(self):
        """Generates a high-level summary of the findings."""
        bandit_results = self.results.get("bandit", {}).get("results", [])
        secrets = self.results.get("secrets", [])

        high_severity = len([i for i in bandit_results if i.get("issue_severity") == "HIGH"])
        medium_severity = len([i for i in bandit_results if i.get("issue_severity") == "MEDIUM"])

        self.results["summary"] = {
            "total_issues": len(bandit_results) + len(secrets),
            "high_severity": high_severity,
            "medium_severity": medium_severity,
            "secrets_found": len(secrets)
        }

    def print_report(self):
        """Prints a readable report to stdout."""
        print("\n=== Security Audit Report ===")
        summary = self.results.get("summary", {})
        print(f"Total Issues: {summary.get('total_issues', 0)}")
        print(f"  - High Severity: {summary.get('high_severity', 0)}")
        print(f"  - Medium Severity: {summary.get('medium_severity', 0)}")
        print(f"  - Secrets Found: {summary.get('secrets_found', 0)}")

        print("\n--- Static Analysis (Bandit) ---")
        bandit_res = self.results.get("bandit", {})
        if "error" in bandit_res:
            print(f"Error running Bandit: {bandit_res['error']}")
        elif not bandit_res.get("results"):
            print("✅ No static analysis issues found.")
        else:
            for issue in bandit_res["results"]:
                sev = issue.get("issue_severity", "UNKNOWN")
                print(f"[{sev}] {issue.get('filename')}:{issue.get('line_number')}")
                print(f"    {issue.get('issue_text')}")
                print(f"    More info: {issue.get('more_info')}")

        print("\n--- Secret Scanning ---")
        if not self.results.get("secrets"):
            print("✅ No potential secrets found.")
        else:
            for secret in self.results["secrets"]:
                print(f"⚠️  {secret}")
        print("=============================\n")
