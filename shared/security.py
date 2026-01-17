import os
import re
import subprocess
import shutil
import json
from pathlib import Path
from typing import List, Dict, Any

class SecurityAuditor:
    """
    Audits the codebase for security vulnerabilities and secrets.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def run_bandit(self, severity: str = "medium") -> Dict[str, Any]:
        """
        Runs bandit static analysis on the project directory.
        Returns a dictionary containing the results.
        """
        bandit_path = shutil.which("bandit")
        if not bandit_path:
            return {"error": "Bandit is not installed or not in PATH."}

        # Severity levels: low, medium, high
        # bandit args: -l (low), -ll (medium), -lll (high)
        severity_map = {
            "low": ["-l"],
            "medium": ["-ll"],
            "high": ["-lll"]
        }
        severity_args = severity_map.get(severity.lower(), ["-ll"])

        # Construct command
        # -r: recursive
        # -f json: output format json
        # -q: quiet (only errors) - wait, -f json might conflict with some output if not quiet
        cmd = [bandit_path, "-r", str(self.project_dir), "-f", "json", "--quiet"] + severity_args

        # Exclude common noisy directories
        cmd.extend(["-x", ".venv,venv,env,.git,__pycache__,tests,build,dist"])

        try:
            # Bandit returns exit code 1 if issues are found, which is annoying for check=True
            result = subprocess.run(cmd, capture_output=True, text=True)

            # If bandit crashes (not just finding issues), stderr might have info
            if result.stderr and not result.stdout:
                 return {"error": f"Bandit execution failed: {result.stderr}"}

            try:
                data = json.loads(result.stdout)
                return data
            except json.JSONDecodeError:
                return {"error": "Failed to parse bandit output", "raw_output": result.stdout}

        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """
        Scans the codebase for potential secrets using regex patterns.
        """
        findings = []

        # Define patterns
        patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "AWS Secret Key": r"(?i)aws_secret_access_key\s*=\s*['\"]([A-Za-z0-9/+=]{40})['\"]",
            "Generic API Key": r"(?i)(api_key|access_token|secret_key|auth_token)\s*=\s*['\"]([A-Za-z0-9_\-]{20,})['\"]",
            "Private Key": r"-----BEGIN PRIVATE KEY-----",
        }

        # Walk through files
        for root, dirs, files in os.walk(self.project_dir):
            # Skip hidden dirs and venvs
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["venv", "env", "__pycache__", "build", "dist"]]

            for file in files:
                if file.startswith("."):
                    continue

                # Skip binary files and likely non-code files
                if file.endswith(('.pyc', '.so', '.o', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz')):
                    continue

                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines):
                        for name, pattern in patterns.items():
                            match = re.search(pattern, line)
                            if match:
                                # Mask the secret for the report
                                secret = match.group(0)
                                if len(secret) > 10:
                                    masked = secret[:4] + "*" * (len(secret) - 8) + secret[-4:]
                                else:
                                    masked = "***"

                                findings.append({
                                    "type": name,
                                    "file": str(file_path.relative_to(self.project_dir)),
                                    "line": i + 1,
                                    "snippet": line.strip().replace(secret, masked),
                                    "severity": "HIGH"
                                })
                except Exception:
                    # Ignore files we can't read
                    continue

        return findings
