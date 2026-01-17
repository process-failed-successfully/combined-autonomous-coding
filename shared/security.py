import subprocess
import re
import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.logger import get_logger

logger = get_logger(__name__)

class SecurityAuditor:
    """
    Audits the codebase for security vulnerabilities using static analysis (Bandit)
    and pattern matching for secrets.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.findings: List[Dict[str, Any]] = []

    def run_bandit_scan(self, severity: str = "medium") -> List[Dict[str, Any]]:
        """
        Runs bandit security scanner on the project directory.
        """
        logger.info(f"Running Bandit security scan on {self.project_dir}...")
        findings = []

        # severity: low, medium, high. bandit uses -l, -ll, -lll
        severity_flags = "-l"
        if severity == "medium":
            severity_flags = "-ll"
        elif severity == "high":
            severity_flags = "-lll"

        cmd = [
            "bandit",
            "-r", str(self.project_dir),
            severity_flags,
            "-f", "json",
            "-q", # quiet
            "-x", ".venv,venv,build,tests,node_modules,.git" # Exclude common dirs
        ]

        try:
            # Bandit returns exit code 1 if issues are found, which is expected.
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    results = data.get("results", [])
                    for item in results:
                        findings.append({
                            "type": "Static Analysis (Bandit)",
                            "check_id": item.get("test_id"),
                            "message": item.get("issue_text"),
                            "file": item.get("filename"),
                            "line": item.get("line_number"),
                            "severity": item.get("issue_severity"),
                            "confidence": item.get("issue_confidence")
                        })
                except json.JSONDecodeError:
                    logger.error("Failed to parse Bandit JSON output.")
                    if result.stderr:
                         logger.error(f"Bandit stderr: {result.stderr}")

        except FileNotFoundError:
            logger.error("Bandit executable not found. Please install it via 'pip install bandit'.")
            findings.append({
                "type": "System Error",
                "message": "Bandit executable not found.",
                "severity": "CRITICAL",
                "file": "N/A",
                "line": 0
            })

        self.findings.extend(findings)
        return findings

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """
        Scans for potential hardcoded secrets using regex patterns.
        """
        logger.info("Scanning for potential secrets...")
        secret_patterns = [
            (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
            (r"sk-[a-zA-Z0-9]{32,}", "OpenAI/Generic Secret Key"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
            (r"xox[baprs]-([0-9a-zA-Z]{10,48})?", "Slack Token"),
            (r"-----BEGIN PRIVATE KEY-----", "Private Key Block"),
            (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
            (r"glpat-[0-9a-zA-Z\-]{20}", "GitLab Personal Access Token"),
        ]

        findings = []

        # We'll use git ls-files if available to respect .gitignore, otherwise os.walk
        files_to_scan = []
        git_path = None
        try:
            import shutil
            git_path = shutil.which("git")
            if git_path and (self.project_dir / ".git").is_dir():
                result = subprocess.run(
                    [git_path, "-C", str(self.project_dir), "ls-files"],
                    capture_output=True, text=True, check=True
                )
                files_to_scan = [self.project_dir / f for f in result.stdout.splitlines() if f]
        except Exception:
            pass

        if not files_to_scan:
            # Fallback to os.walk
            for root, dirs, files in os.walk(self.project_dir):
                # Filter out hidden/ignored directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__']]
                for file in files:
                    if file.startswith('.'): continue
                    files_to_scan.append(Path(root) / file)

        for file_path in files_to_scan:
            # Skip binary files, lock files, etc
            if file_path.suffix in ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.pyc', '.lock', '.sqlite', '.db']:
                continue

            # Skip large files > 1MB
            try:
                if file_path.stat().st_size > 1024 * 1024:
                    continue
            except OSError:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, 1):
                        for pattern, name in secret_patterns:
                            if re.search(pattern, line):
                                findings.append({
                                    "type": "Secret Detection",
                                    "message": f"Potential {name} found.",
                                    "file": str(file_path.relative_to(self.project_dir)),
                                    "line": i,
                                    "severity": "HIGH",
                                    "match_preview": line.strip()[:50] + "..." # Truncate for safety
                                })
            except (IOError, OSError):
                continue

        self.findings.extend(findings)
        return findings

    def generate_report(self) -> str:
        """
        Generates a readable report from the findings.
        """
        if not self.findings:
            return "✅ No security issues found."

        report = [f"🛡️ Security Audit Report"]
        report.append(f"Target: {self.project_dir}")
        report.append(f"Total Issues: {len(self.findings)}")
        report.append("-" * 60)

        # Group by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNDEFINED": 4}

        sorted_findings = sorted(
            self.findings,
            key=lambda x: severity_order.get((x.get("severity") or "UNDEFINED").upper(), 4)
        )

        for f in sorted_findings:
            severity = (f.get('severity') or 'UNKNOWN').upper()
            icon = "🔴" if severity in ["HIGH", "CRITICAL"] else "🟠" if severity == "MEDIUM" else "🔵"

            report.append(f"{icon} [{severity}] {f['type']}")
            report.append(f"   File: {f['file']}:{f['line']}")
            report.append(f"   Message: {f['message']}")
            if f.get('confidence'):
                report.append(f"   Confidence: {f['confidence']}")
            report.append("")

        return "\n".join(report)
