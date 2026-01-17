import json
import subprocess
import re
import sys
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

@dataclass
class SecurityIssue:
    check_id: str
    description: str
    filename: str
    line_number: int
    severity: str
    confidence: str
    code: Optional[str] = None
    remediation: Optional[str] = None

    def to_dict(self):
        return asdict(self)

class SecurityAuditor:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def run_bandit(self, severity: str = "low", confidence: str = "low") -> List[SecurityIssue]:
        """Runs bandit on the project directory."""

        # Map severity/confidence strings to bandit flags if needed,
        # but bandit uses -l (low), -ll (medium), -lll (high) for severity
        # and -i (low), -ii (medium), -iii (high) for confidence.
        # Actually, newer bandit versions support --severity-level {low,medium,high}
        # Let's try to use the argument flags which are clearer.

        cmd = [
            "bandit",
            "-r", str(self.project_dir),
            "-f", "json",
            "--severity-level", severity.lower(),
            "--confidence-level", confidence.lower(),
            "--exclude", "*/.venv/*,*/tests/*,*/venv/*,*/env/*"
        ]

        try:
            # Bandit returns exit code 1 if issues are found, so check=False
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = result.stdout.strip()

            # If output is empty, something went wrong (or just stderr)
            if not output:
                if result.stderr:
                    print(f"Bandit error: {result.stderr}", file=sys.stderr)
                return []

            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                print(f"Failed to decode bandit output: {output[:200]}...", file=sys.stderr)
                return []

            issues = []
            for result_item in data.get("results", []):
                issue = SecurityIssue(
                    check_id=result_item.get("test_id", "UNKNOWN"),
                    description=result_item.get("issue_text", ""),
                    filename=result_item.get("filename", ""),
                    line_number=result_item.get("line_number", 0),
                    severity=result_item.get("issue_severity", "UNKNOWN"),
                    confidence=result_item.get("issue_confidence", "UNKNOWN"),
                    code=result_item.get("code", "").strip(),
                    remediation=result_item.get("more_info", "")
                )
                issues.append(issue)

            return issues

        except FileNotFoundError:
            print("Error: 'bandit' command not found. Please install it.", file=sys.stderr)
            return []
        except Exception as e:
            print(f"An error occurred while running bandit: {e}", file=sys.stderr)
            return []

    def scan_secrets(self) -> List[SecurityIssue]:
        """Scans for potential secrets/keys in the codebase."""
        issues = []

        # Simple regex patterns for common secrets
        patterns = {
            "AWS Access Key": r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
            "Generic Private Key": r"-----BEGIN (?:RSA|DSA|EC|PGP|OPENSSH) PRIVATE KEY-----",
            "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})?",
            "GitHub Token": r"(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}",
            "Google API Key": r"AIza[0-9A-Za-z\\-_]{35}",
        }

        # Walk through files
        # Using git ls-files if available is safer to avoid ignored files,
        # but os.walk with exclusion is a fallback.
        # Let's reuse shared.utils functionality if possible, but keeping it simple here.

        git_exists = subprocess.run(["which", "git"], capture_output=True).returncode == 0
        files_to_scan = []

        if git_exists and (self.project_dir / ".git").exists():
            try:
                res = subprocess.run(
                    ["git", "ls-files"],
                    cwd=str(self.project_dir),
                    capture_output=True,
                    text=True,
                    check=True
                )
                files_to_scan = [self.project_dir / f for f in res.stdout.splitlines()]
            except subprocess.CalledProcessError:
                pass

        if not files_to_scan:
            # Fallback to os.walk
            for root, dirs, files in os.walk(self.project_dir):
                # Simple exclusion
                dirs[:] = [d for d in dirs if d not in {'.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules'}]
                for file in files:
                    files_to_scan.append(Path(root) / file)

        for filepath in files_to_scan:
            try:
                # Skip non-text files or very large files
                if filepath.stat().st_size > 1024 * 1024: # Skip > 1MB
                    continue

                # Check extension blacklist?
                if filepath.suffix in {'.pyc', '.so', '.o', '.class', '.exe', '.dll', '.png', '.jpg', '.jpeg', '.gif', '.ico'}:
                    continue

                content = filepath.read_text(errors='ignore')

                for secret_name, pattern in patterns.items():
                    # Simple findall
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # Determine line number
                        # This is inefficient for large files with many matches, but okay for secret scanning
                        line_number = content.count('\n', 0, match.start()) + 1
                        matched_text = match.group(0)

                        # Obfuscate the secret in the output
                        masked_secret = matched_text[:4] + "*" * (len(matched_text) - 4)

                        issue = SecurityIssue(
                            check_id="SECRET-SCAN",
                            description=f"Potential {secret_name} found: {masked_secret}",
                            filename=str(filepath.relative_to(self.project_dir)),
                            line_number=line_number,
                            severity="HIGH",
                            confidence="MEDIUM",
                            code=matched_text, # Be careful exposing this! Maybe mask it here too.
                            remediation="Remove the secret from the codebase and revoke it immediately."
                        )
                        # Override code with masked version for safety
                        issue.code = masked_secret
                        issues.append(issue)

            except Exception:
                # Ignore read errors
                pass

        return issues

    def run_security_scan(self, scan_type: str = "all", severity: str = "low", confidence: str = "low") -> List[SecurityIssue]:
        all_issues = []

        if scan_type in ["all", "static"]:
            print("Running static analysis (Bandit)...")
            all_issues.extend(self.run_bandit(severity, confidence))

        if scan_type in ["all", "secrets"]:
            print("Running secret scanning...")
            all_issues.extend(self.scan_secrets())

        return all_issues
