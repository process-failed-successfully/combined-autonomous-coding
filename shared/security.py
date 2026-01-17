"""
Security Auditor
================

Provides security scanning capabilities using Bandit (SAST) and custom secret detection.
"""

import os
import re
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SecurityAuditor:
    """
    Audits the codebase for security vulnerabilities and secrets.
    """

    # Regex patterns for secret detection
    SECRET_PATTERNS = {
        "AWS Access Key": r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])",  # broad pattern, refine if needed. commonly AKIA...
        "AWS Secret Key": r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])",
        "Private Key": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
        "Generic API Key": r"api_key\s*[:=]\s*['\"]([A-Za-z0-9_\-]{20,})['\"]",
        "Generic Secret": r"secret\s*[:=]\s*['\"]([A-Za-z0-9_\-]{20,})['\"]",
    }

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def _mask_secret(self, text: str) -> str:
        """Masks a secret string, revealing only the first 4 and last 4 characters."""
        if len(text) <= 8:
            return "*" * len(text)
        return text[:4] + "*" * (len(text) - 8) + text[-4:]

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """
        Scans the project directory for potential secrets using regex patterns.
        """
        findings = []

        # Using os.walk for full python regex support
        for root, dirs, files in os.walk(self.project_dir):
            # Skip common ignored dirs
            dirs[:] = [d for d in dirs if d not in {'.git', '.venv', 'venv', '__pycache__', 'node_modules', '.idea', '.vscode'}]

            for file in files:
                if file.endswith(('.pyc', '.so', '.o', '.class', '.db', '.sqlite')):
                    continue

                file_path = Path(root) / file
                try:
                    # Read file with error handling
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for name, pattern in self.SECRET_PATTERNS.items():
                        for match in re.finditer(pattern, content):
                            matched_text = match.group(0)
                            # For capture groups (like Generic API Key), we might want just the group.
                            # But finditer returns match objects.
                            # If the pattern has groups, usually we want the secret part.
                            if match.groups():
                                matched_text = match.group(1)

                            # specific check for AKIA to reduce false positives on the "AWS Access Key" pattern
                            if name == "AWS Access Key" and not matched_text.startswith("AKIA"):
                                    continue

                            findings.append({
                                "type": "secret",
                                "check_id": name.replace(" ", "_").upper(),
                                "path": str(file_path.relative_to(self.project_dir)),
                                "line": content[:match.start()].count('\n') + 1,
                                "severity": "HIGH",
                                "message": f"Potential {name} detected.",
                                "code": self._mask_secret(matched_text)
                            })
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")

        return findings

    def run_bandit(self, severity: str = "LOW") -> List[Dict[str, Any]]:
        """
        Runs Bandit SAST scan on the project.
        """
        bandit_path = shutil.which("bandit")
        if not bandit_path:
            logger.warning("Bandit not found. Skipping SAST scan.")
            return []

        # Map CLI severity to bandit arguments
        # Memory: "use the --severity-level argument with lowercase values ('low', 'medium', 'high')"
        severity_map = {
            "LOW": "low",
            "MEDIUM": "medium",
            "HIGH": "high"
        }
        level = severity_map.get(severity.upper(), "low")

        cmd = [
            bandit_path,
            "-r", str(self.project_dir),
            "-f", "json",
            "--severity-level", level,
            "--quiet", # Memory: "must be included to suppress progress bars"
            "--exit-zero", # Don't crash subprocess on findings
            "-x", ".venv,venv,tests" # Exclude common dirs
        ]

        # Use .bandit or pyproject.toml if available?
        # For now, default args.

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=os.environ.copy() # Memory: "use os.environ.copy() to preserve PATH"
            )

            if not result.stdout.strip():
                return []

            try:
                data = json.loads(result.stdout)
                results = data.get("results", [])

                # Transform to common format
                findings = []
                for item in results:
                    findings.append({
                        "type": "sast",
                        "check_id": item.get("test_id"),
                        "path": item.get("filename"), # Bandit returns absolute paths sometimes?
                        "line": item.get("line_number"),
                        "severity": item.get("issue_severity"),
                        "message": item.get("issue_text"),
                        "code": item.get("code")
                    })
                return findings

            except json.JSONDecodeError:
                logger.error("Failed to parse Bandit output JSON.")
                return []

        except Exception as e:
            logger.error(f"Error running Bandit: {e}")
            return []

    def run_security_scan(self, scan_type: str = "all", severity: str = "LOW") -> List[Dict[str, Any]]:
        """
        Orchestrates the security scan based on type.
        """
        findings = []

        if scan_type in ["all", "secrets"]:
            logger.info("Running Secret Scan...")
            findings.extend(self.scan_secrets())

        if scan_type in ["all", "bandit"]:
            logger.info("Running Bandit SAST Scan...")
            findings.extend(self.run_bandit(severity))

        return findings

    def generate_report(self, findings: List[Dict[str, Any]]) -> str:
        """
        Generates a markdown report from findings.
        """
        if not findings:
            return "✅ No security issues found."

        report = [
            "# Security Audit Report",
            f"\nFound {len(findings)} issues.",
            "\n| Severity | Type | File | Line | Message |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]

        # Sort by severity (HIGH > MEDIUM > LOW)
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "UNDEFINED": 3}
        findings.sort(key=lambda x: severity_order.get(x.get("severity", "UNDEFINED").upper(), 3))

        for f in findings:
            # Handle path display (make relative if absolute)
            path = f.get('path', 'unknown')
            if str(path).startswith(str(self.project_dir)):
                try:
                    path = Path(path).relative_to(self.project_dir)
                except ValueError:
                    pass

            severity = (f.get("severity") or "UNKNOWN").upper()
            msg = f.get("message", "").replace("\n", " ")

            report.append(f"| {severity} | {f.get('type')} | {path} | {f.get('line')} | {msg} |")

        return "\n".join(report)
