import os
import re
import subprocess
import shutil
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class SecurityAuditor:
    """
    Audits the project for security vulnerabilities using static analysis (Bandit)
    and custom secret scanning.
    """

    # Regex patterns for secret detection
    SECRET_PATTERNS = {
        "AWS Access Key": r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])",
        "AWS Secret Key": r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])",
        "Private Key": r"-----BEGIN [A-Z]+ PRIVATE KEY-----",
        "Generic API Key": r"['\"](api_key|apikey|secret|token)['\"]\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{20,})['\"]",
    }

    # AWS Access Key IDs usually start with AKIA, ASIA, AIDA, AROA
    AWS_KEY_PREFIXES = ("AKIA", "ASIA", "AIDA", "AROA")

    def __init__(self):
        pass

    def scan_secrets(self, project_dir: Path) -> List[Dict[str, Any]]:
        """
        Scans the project directory for potential secrets using regex patterns.
        """
        findings = []
        project_dir = project_dir.resolve()

        # Files/Dirs to skip
        skip_dirs = {'.git', '.venv', 'venv', 'env', '__pycache__', '.mypy_cache', '.pytest_cache', 'node_modules'}
        skip_extensions = {'.pyc', '.so', '.db', '.sqlite', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz'}

        for root, dirs, files in os.walk(project_dir):
            # Modify dirs in-place to skip specific directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in skip_extensions:
                    continue

                try:
                    # Read file with error handling for non-text files
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    for line_num, line in enumerate(content.splitlines(), 1):
                        for name, pattern in self.SECRET_PATTERNS.items():
                            matches = re.finditer(pattern, line)
                            for match in matches:
                                secret_candidate = match.group(0)

                                # Specific validation for AWS Access Keys
                                if name == "AWS Access Key":
                                    if not secret_candidate.startswith(self.AWS_KEY_PREFIXES):
                                        continue

                                # Specific validation/extraction for Generic API Keys
                                if name == "Generic API Key":
                                    # The regex captures the key value in group 2
                                    secret_candidate = match.group(2)

                                # Mask the secret for the report
                                masked_secret = self._mask_secret(secret_candidate)
                                snippet = line.replace(secret_candidate, masked_secret).strip()

                                findings.append({
                                    "type": "secret",
                                    "check_id": f"SECRET_{name.upper().replace(' ', '_')}",
                                    "severity": "HIGH",
                                    "filename": str(file_path.relative_to(project_dir)),
                                    "line_number": line_num,
                                    "issue_text": f"Potential {name} found.",
                                    "snippet": snippet
                                })
                except Exception as e:
                    # Log error but continue scanning
                    # print(f"Error scanning file {file_path}: {e}")
                    pass

        return findings

    def _mask_secret(self, secret: str) -> str:
        """Masks a secret string for safe display."""
        if len(secret) <= 4:
            return "*" * len(secret)
        return secret[:2] + "*" * (len(secret) - 4) + secret[-2:]

    def run_bandit(self, project_dir: Path, severity: str = "LOW") -> List[Dict[str, Any]]:
        """
        Runs Bandit static analysis on the project directory.
        """
        bandit_path = shutil.which("bandit")
        if not bandit_path:
            return [{
                "type": "error",
                "severity": "HIGH",
                "issue_text": "Bandit is not installed. Skipping static analysis."
            }]

        severity_flag = "-l"  # Low (default)
        if severity.upper() == "MEDIUM":
            severity_flag = "-ll"
        elif severity.upper() == "HIGH":
            severity_flag = "-lll"

        try:
            # We use --quiet to avoid progress bars messing up JSON output if we were parsing stdout manually,
            # but here we use -f json.
            cmd = [
                bandit_path,
                "-r", str(project_dir),
                "-f", "json",
                "--quiet",
                severity_flag,
                # Exclude tests directory by default as it often contains hardcoded "secrets" for testing
                "--exclude", "tests/,*/tests/"
            ]

            # Bandit returns exit code 1 if issues are found, so check=False
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    results = data.get("results", [])
                    # Normalize keys
                    for r in results:
                        r["type"] = "bandit"
                        r["severity"] = r.get("issue_severity", "UNKNOWN")
                    return results
                except json.JSONDecodeError:
                    return [{
                        "type": "error",
                        "severity": "HIGH",
                        "issue_text": f"Failed to parse Bandit JSON output: {result.stdout[:100]}..."
                    }]

            if result.returncode != 0 and not result.stdout:
                 return [{
                    "type": "error",
                    "severity": "HIGH",
                    "issue_text": f"Bandit failed with error: {result.stderr}"
                }]

            return []

        except Exception as e:
            return [{
                "type": "error",
                "severity": "HIGH",
                "issue_text": f"Exception while running Bandit: {str(e)}"
            }]

    def run_security_scan(self, project_dir: Path, scan_type: str = "all", severity: str = "LOW") -> Dict[str, Any]:
        """
        Orchestrates the security scan.
        """
        all_findings = []

        if scan_type in ("all", "secrets"):
            all_findings.extend(self.scan_secrets(project_dir))

        if scan_type in ("all", "bandit"):
            all_findings.extend(self.run_bandit(project_dir, severity))

        # Filter by severity if needed (though bandit already filters, secrets are always HIGH)
        # Implementation detail: Bandit flags are mapped, but we can double check here or just return all.

        return {
            "findings": all_findings,
            "summary": {
                "total": len(all_findings),
                "high": sum(1 for f in all_findings if f.get('severity', '').upper() == 'HIGH'),
                "medium": sum(1 for f in all_findings if f.get('severity', '').upper() == 'MEDIUM'),
                "low": sum(1 for f in all_findings if f.get('severity', '').upper() == 'LOW'),
            }
        }
