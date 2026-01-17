import subprocess
import re
import json
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SecurityAuditor:
    """
    Audits the codebase for security vulnerabilities using static analysis (Bandit)
    and secret scanning.
    """

    # Common secret patterns
    SECRET_PATTERNS = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "AWS Secret Key": r"(?i)aws_secret_access_key.{0,20}['\"][0-9a-zA-Z\/+]{40}['\"]",
        "Generic API Key": r"(?i)(api_key|access_token|secret_key).{0,20}['\"][0-9a-zA-Z\-_]{16,64}['\"]",
        "Private Key": r"-----BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----",
    }

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.findings: List[Dict[str, Any]] = []

    def run_bandit(self, severity: str = "medium", confidence: str = "medium") -> List[Dict[str, Any]]:
        """
        Runs Bandit static analysis on the project directory.
        """
        bandit_path = shutil.which("bandit")
        if not bandit_path:
            logger.warning("Bandit not found. Skipping static analysis.")
            return []

        # Map severity/confidence to bandit flags
        sev_flag = "-ll" # default medium
        if severity == "low": sev_flag = "-l"
        elif severity == "high": sev_flag = "-lll"

        conf_flag = "-ii" # default medium
        if confidence == "low": conf_flag = "-i"
        elif confidence == "high": conf_flag = "-iii"

        # Exclude common dirs
        excludes = ".venv,venv,build,dist,tests,node_modules,.git"

        cmd = [
            bandit_path,
            "-r", str(self.project_dir),
            "-f", "json",
            sev_flag,
            conf_flag,
            "-x", excludes
        ]

        logger.info(f"Running bandit: {' '.join(cmd)}")

        try:
            # Bandit returns exit code 1 if issues are found, which is expected.
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    results = data.get("results", [])

                    # Convert to our format
                    bandit_findings = []
                    for item in results:
                        finding = {
                            "type": "Static Analysis (Bandit)",
                            "check_id": item.get("test_id"),
                            "description": item.get("issue_text"),
                            "file": item.get("filename"),
                            "line": item.get("line_number"),
                            "severity": item.get("issue_severity"),
                            "confidence": item.get("issue_confidence"),
                            "code": item.get("code")
                        }
                        bandit_findings.append(finding)

                    self.findings.extend(bandit_findings)
                    return bandit_findings
                except json.JSONDecodeError:
                    logger.error("Failed to parse bandit JSON output.")
                    return []
            return []

        except Exception as e:
            logger.error(f"Error running bandit: {e}")
            return []

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """
        Scans files for potential secrets using regex patterns.
        """
        secret_findings = []

        # Exclude binary files and common ignores
        exclude_dirs = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'build', 'dist'}

        for path in self.project_dir.rglob("*"):
            if not path.is_file():
                continue

            # Skip excluded dirs
            if any(part in exclude_dirs for part in path.parts):
                continue

            # Skip large files (> 1MB)
            if path.stat().st_size > 1024 * 1024:
                continue

            try:
                content = path.read_text(errors="ignore")

                for name, pattern in self.SECRET_PATTERNS.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # Calculate line number
                        line_number = content[:match.start()].count('\n') + 1

                        finding = {
                            "type": "Secret Scan",
                            "check_id": "SECRET_REGEX",
                            "description": f"Potential {name} found",
                            "file": str(path.relative_to(self.project_dir)),
                            "line": line_number,
                            "severity": "HIGH",
                            "confidence": "Medium",
                            "code": match.group(0)[:20] + "..." # Truncate secret
                        }
                        secret_findings.append(finding)
            except Exception as e:
                logger.warning(f"Error scanning file {path}: {e}")

        self.findings.extend(secret_findings)
        return secret_findings

    def generate_report(self) -> str:
        """
        Generates a readable report from the findings.
        """
        if not self.findings:
            return "✅ No security issues found."

        report = [f"⚠️ Security Audit Report: {len(self.findings)} issues found\n"]

        # Group by type
        bandit_issues = [f for f in self.findings if "Bandit" in f["type"]]
        secret_issues = [f for f in self.findings if "Secret" in f["type"]]

        if bandit_issues:
            report.append(f"--- Static Analysis ({len(bandit_issues)}) ---")
            for i, issue in enumerate(bandit_issues, 1):
                report.append(f"{i}. [{issue['severity']}] {issue['description']}")
                report.append(f"   File: {issue['file']}:{issue['line']}")
                report.append(f"   Code: {issue['code'].strip() if issue.get('code') else 'N/A'}")
                report.append("")

        if secret_issues:
            report.append(f"--- Secret Scan ({len(secret_issues)}) ---")
            for i, issue in enumerate(secret_issues, 1):
                report.append(f"{i}. [{issue['severity']}] {issue['description']}")
                report.append(f"   File: {issue['file']}:{issue['line']}")
                report.append("")

        return "\n".join(report)
