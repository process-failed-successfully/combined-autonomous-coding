import os
import re
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.utils import IGNORED_DIRS

logger = logging.getLogger(__name__)

class SecurityAuditor:
    """
    Audits the project for security vulnerabilities using static analysis (bandit)
    and secret scanning.
    """

    # Common patterns for secret detection
    SECRET_PATTERNS = {
        "AWS Access Key": r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "Private Key": r"-----BEGIN .* PRIVATE KEY-----",
        "Generic API Key": r"(?i)(api_key|access_token|secret)[a-zA-Z0-9_]*\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
        "GitHub Token": r"gh[pousr]_[a-zA-Z0-9]{36,}"
    }

    def __init__(self):
        pass

    def run_bandit(self, project_dir: Path, severity: str = "medium") -> Dict[str, Any]:
        """
        Runs bandit on the project directory.
        Returns a dictionary with the results.
        """
        import shutil
        bandit_path = shutil.which("bandit")
        if not bandit_path:
            return {"error": "Bandit tool not found. Please install it (pip install bandit).", "results": []}

        cmd = [
            bandit_path,
            "-r", str(project_dir),
            "-f", "json",
            "--severity-level", severity.lower(),
            "--exit-zero"  # Don't fail the subprocess, we want to parse the output
        ]

        # Ignore common test/build dirs
        exclude_dirs = [".venv", "venv", "tests", ".git", "node_modules"]
        cmd.extend(["-x", ",".join(exclude_dirs)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse bandit output.", "raw_output": result.stdout, "results": []}
            return {"results": []}
        except Exception as e:
            return {"error": f"Error running bandit: {str(e)}", "results": []}

    def scan_secrets(self, project_dir: Path) -> List[Dict[str, Any]]:
        """
        Scans the project for secrets using regex patterns.
        """
        findings = []

        # Try to use git ls-files to respect .gitignore
        files_to_scan = []
        git_path = subprocess.run(["which", "git"], capture_output=True, text=True).stdout.strip()

        use_git = False
        if git_path and (project_dir / ".git").is_dir():
            try:
                result = subprocess.run(
                    [git_path, "-C", str(project_dir), "ls-files"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    files_to_scan = [project_dir / f for f in result.stdout.splitlines()]
                    use_git = True
            except Exception:
                pass

        if not use_git:
            # Fallback to os.walk
            for root, dirs, files in os.walk(project_dir):
                # Prune ignored dirs
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and d not in [".git", ".venv", "venv"]]

                for filename in files:
                    files_to_scan.append(Path(root) / filename)

        for file_path in files_to_scan:
            # Skip if file doesn't exist (deleted since ls-files) or is not a file
            if not file_path.exists() or not file_path.is_file():
                continue

            # Skip large files (>1MB) to avoid performance issues
            try:
                if file_path.stat().st_size > 1024 * 1024:
                    continue
            except OSError:
                continue

            try:
                # Read file content. Attempt utf-8, fallback to ignore errors (binary files)
                try:
                    content = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue # Skip binary files

                for name, pattern in self.SECRET_PATTERNS.items():
                    for match in re.finditer(pattern, content):
                        # Construct a snippet (masking the secret)
                        start, end = match.span()
                        line_no = content.count('\n', 0, start) + 1
                        secret_val = match.group(0)
                        masked_val = secret_val[:4] + "*" * (len(secret_val) - 8) + secret_val[-4:] if len(secret_val) > 8 else "****"

                        findings.append({
                            "type": name,
                            "file": str(file_path.relative_to(project_dir)),
                            "line": line_no,
                            "match": masked_val
                        })
            except Exception as e:
                logger.warning(f"Error scanning file {file_path}: {e}")

        return findings

    def audit_project(self, project_dir: Path, scan_type: str = "all", severity: str = "medium") -> Dict[str, Any]:
        """
        Runs the security audit.
        scan_type: "all", "static", "secrets"
        severity: "low", "medium", "high"
        """
        report = {
            "static_analysis": {},
            "secrets": [],
            "summary": {"issues_found": 0}
        }

        if scan_type in ["all", "static"]:
            logger.info("Running static analysis (Bandit)...")
            bandit_results = self.run_bandit(project_dir, severity)
            report["static_analysis"] = bandit_results
            if "results" in bandit_results:
                report["summary"]["issues_found"] += len(bandit_results["results"])

        if scan_type in ["all", "secrets"]:
            logger.info("Scanning for secrets...")
            secrets_found = self.scan_secrets(project_dir)
            report["secrets"] = secrets_found
            report["summary"]["issues_found"] += len(secrets_found)

        return report
