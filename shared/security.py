import subprocess
import re
import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any

class SecurityAuditor:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.findings = []

    def run_bandit(self, severity: str = "LOW") -> List[Dict[str, Any]]:
        """Runs bandit security scan."""
        if not shutil.which("bandit"):
            return [{"tool": "bandit", "type": "error", "message": "Bandit is not installed. Please run 'pip install bandit'."}]

        severity_flag = "-l" # Low
        if severity.upper() == "MEDIUM":
            severity_flag = "-ll"
        elif severity.upper() == "HIGH":
            severity_flag = "-lll"

        try:
            # -f json to get parseable output
            # -r for recursive
            # --quiet to suppress output
            # -x to exclude paths
            cmd = ["bandit", "-r", str(self.project_dir), "-f", "json", severity_flag, "--quiet", "-x", ".venv,venv,.git,__pycache__,tests"]

            result = subprocess.run(cmd, capture_output=True, text=True)

            # Bandit returns exit code 1 if issues are found, which is fine.
            # We parse the JSON output.

            if not result.stdout.strip():
                 return []

            try:
                data = json.loads(result.stdout)
                results = data.get("results", [])
                formatted_results = []
                for item in results:
                    formatted_results.append({
                        "tool": "bandit",
                        "severity": item.get("issue_severity"),
                        "file": item.get("filename"),
                        "line": item.get("line_number"),
                        "message": item.get("issue_text"),
                        "code": item.get("code"),
                        "link": item.get("issue_cwe").get("link") if item.get("issue_cwe") else None,
                        "suggestion": "Review the code snippet and apply the recommended fix from the documentation."
                    })
                return formatted_results
            except json.JSONDecodeError:
                # If stdout isn't JSON, maybe something went wrong
                return [{"tool": "bandit", "type": "error", "message": "Failed to parse bandit output", "details": result.stdout}]

        except Exception as e:
            return [{"tool": "bandit", "type": "error", "message": f"Error running bandit: {str(e)}"}]

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """Scans for potential secrets."""
        secrets_patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "AWS Secret Key": r"(?i)aws_secret_access_key.{0,20}=.{0,20}[a-zA-Z0-9\/+]{40}",
            # Require quotes for generic keys to avoid matching variable assignments to function calls
            "Generic API Key": r"(?i)(api_key|apikey|secret|token).{0,20}=\s*['\"][a-zA-Z0-9]{16,}['\"]",
            "Private Key": r"-----BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----"
        }

        findings = []

        # Walk through the project directory
        for root, dirs, files in os.walk(self.project_dir):
            # Skip common ignore dirs
            dirs[:] = [d for d in dirs if d not in [".git", ".venv", "venv", "__pycache__", ".agent_trash", ".agent_archives", "tests"]]

            for file in files:
                if file.endswith(('.pyc', '.so', '.o', '.exe', '.db', '.sqlite', '.log')):
                    continue

                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines):
                        for name, pattern in secrets_patterns.items():
                            if re.search(pattern, line):
                                # Mask the secret in the snippet
                                snippet = line.strip()
                                match = re.search(pattern, snippet)
                                if match:
                                    start, end = match.span()
                                    matched_text = snippet[start:end]
                                    if matched_text.startswith("AKIA"):
                                         masked_text = "AKIA" + "*" * (len(matched_text) - 4)
                                    else:
                                         masked_text = "*" * len(matched_text)

                                    masked_snippet = snippet[:start] + masked_text + snippet[end:]
                                else:
                                    masked_snippet = snippet[:100]

                                findings.append({
                                    "tool": "secret-scanner",
                                    "severity": "HIGH",
                                    "file": str(file_path.relative_to(self.project_dir)),
                                    "line": i + 1,
                                    "message": f"Potential {name} detected",
                                    "snippet": masked_snippet,
                                    "suggestion": "Store secrets in environment variables or a secure vault. Do not commit them."
                                })
                except Exception:
                    # Skip files that can't be read
                    continue

        return findings

    def run_all(self, severity: str = "LOW") -> List[Dict[str, Any]]:
        all_findings = []
        all_findings.extend(self.run_bandit(severity))
        all_findings.extend(self.scan_secrets())
        self.findings = all_findings
        return all_findings
