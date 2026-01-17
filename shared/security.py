import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.logger import get_logger

logger = get_logger()

@dataclass
class SecurityFinding:
    type: str  # 'static' or 'secret'
    severity: str
    description: str
    file_path: str
    line_number: int
    code: Optional[str] = None
    more_info: Optional[str] = None

@dataclass
class SecurityReport:
    findings: List[SecurityFinding] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def add_finding(self, finding: SecurityFinding):
        self.findings.append(finding)
        self.summary[finding.severity] = self.summary.get(finding.severity, 0) + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "findings": [
                {
                    "type": f.type,
                    "severity": f.severity,
                    "description": f.description,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "code": f.code,
                    "more_info": f.more_info
                }
                for f in self.findings
            ]
        }

class SecurityAuditor:
    """
    Audits the project for security vulnerabilities using static analysis and secret scanning.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.report = SecurityReport()

    def run_security_scan(self, scan_type: str = "all", severity: str = "medium") -> SecurityReport:
        """
        Runs the security scan.
        :param scan_type: 'all', 'static', or 'secrets'
        :param severity: 'low', 'medium', 'high'
        """
        if scan_type in ["all", "static"]:
            self.scan_static(severity)

        if scan_type in ["all", "secrets"]:
            self.scan_secrets()

        return self.report

    def scan_static(self, severity: str = "medium"):
        """Runs bandit for static analysis."""
        bandit_path = shutil.which("bandit")
        if not bandit_path:
            logger.warning("Bandit not found. Skipping static analysis.")
            return

        logger.info("Running static code analysis (Bandit)...")

        cmd = [
            bandit_path,
            "-r", str(self.project_dir),
            "-f", "json",
            "--quiet",
            "--severity-level", severity.lower()
        ]

        # Check for baseline
        baseline_file = self.project_dir / "bandit_baseline.json"
        if baseline_file.exists():
            cmd.extend(["-b", str(baseline_file)])

        # Exclude common test and virtualenv directories
        cmd.extend(["-x", ".venv,venv,tests,node_modules,.git"])

        try:
            # Bandit returns exit code 1 if issues are found, so check=False
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    for result in data.get("results", []):
                        finding = SecurityFinding(
                            type="static",
                            severity=result.get("issue_severity", "UNKNOWN").upper(),
                            description=result.get("issue_text", ""),
                            file_path=result.get("filename", "").replace(str(self.project_dir) + "/", ""),
                            line_number=result.get("line_number", 0),
                            code=result.get("code", "").strip(),
                            more_info=result.get("more_info")
                        )
                        self.report.add_finding(finding)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse bandit output: {result.stdout}")

            if result.stderr:
                logger.debug(f"Bandit stderr: {result.stderr}")

        except Exception as e:
            logger.error(f"Error running bandit: {e}")

    def scan_secrets(self):
        """Scans for potential secrets/keys using regex patterns."""
        logger.info("Running secret scanning...")

        # Common patterns for secrets
        patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "Google API Key": r"AIza[0-9A-Za-z\\-_]{35}",
            "Generic Private Key": r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
            "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})?",
            "GitHub Personal Access Token": r"ghp_[0-9a-zA-Z]{36}",
            "Generic API Key": r"(?i)(api_key|apikey|secret|token)[\s]*[:=][\s]*['\"][0-9a-zA-Z\-_]{16,}['\"]"
        }

        # Get list of files to scan (respecting gitignore if possible)
        files_to_scan = self._list_files()

        for file_path in files_to_scan:
            try:
                # Skip binary files or very large files
                if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
                    continue

                # Check for binary content
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError:
                    continue  # Skip binary file

                for name, pattern in patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # Mask the secret in the output
                        secret = match.group(0)
                        masked = secret[:4] + "*" * (len(secret) - 8) + secret[-4:] if len(secret) > 8 else "****"

                        # Calculate line number
                        line_number = content[:match.start()].count('\n') + 1

                        finding = SecurityFinding(
                            type="secret",
                            severity="HIGH",
                            description=f"Potential {name} detected",
                            file_path=str(file_path.relative_to(self.project_dir)),
                            line_number=line_number,
                            code=f"Found match: {masked}",
                            more_info="Do not commit secrets to version control."
                        )
                        self.report.add_finding(finding)

            except Exception as e:
                logger.debug(f"Error scanning file {file_path}: {e}")

    def _list_files(self) -> List[Path]:
        """Lists files to scan, preferring git ls-files but falling back to os walk."""
        files = []
        git_path = shutil.which("git")

        if git_path and (self.project_dir / ".git").exists():
            try:
                result = subprocess.run(
                    [git_path, "-C", str(self.project_dir), "ls-files"],
                    capture_output=True, text=True, check=True
                )
                for line in result.stdout.splitlines():
                    path = self.project_dir / line
                    if path.is_file():
                        files.append(path)
                return files
            except subprocess.CalledProcessError:
                pass # Fallback

        # Fallback to os.walk, excluding common ignored dirs
        ignored_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".agent_trash", ".agent_archives"}

        for root, dirs, filenames in os.walk(self.project_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignored_dirs]

            for filename in filenames:
                path = Path(root) / filename
                files.append(path)

        return files
