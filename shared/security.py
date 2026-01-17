import subprocess
import json
import re
import shutil
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

class SecurityAuditor:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.bandit_path = shutil.which("bandit")

    def run_bandit(self, severity: str = "LOW") -> List[Dict[str, Any]]:
        """Runs bandit security analysis."""
        if not self.bandit_path:
            return [{"error": "Bandit is not installed. Install it with `pip install bandit`."}]

        # Map severity to bandit flags
        severity_map = {
            "LOW": "low",
            "MEDIUM": "medium",
            "HIGH": "high"
        }
        severity_level = severity_map.get(severity.upper(), "low")

        try:
            # -f json to get JSON output
            # -r to recursive
            # --quiet to suppress output
            # --severity-level to filter by severity
            cmd = [
                self.bandit_path,
                "-r", str(self.project_dir),
                "-f", "json",
                "--quiet",
                "--severity-level", severity_level
            ]

            # Bandit returns 1 if issues are found, 0 if not.
            # We capture output regardless.
            result = subprocess.run(cmd, capture_output=True, text=True)

            if not result.stdout.strip():
                return []

            try:
                data = json.loads(result.stdout)
                return data.get("results", [])
            except json.JSONDecodeError:
                return [{"error": "Failed to parse bandit output", "raw": result.stdout}]

        except Exception as e:
            return [{"error": str(e)}]

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """Scans for potential secrets using regex patterns."""
        findings = []

        # Regex patterns for common secrets
        # Format: "Name": (regex_pattern, is_case_insensitive)
        patterns = {
            "AWS Access Key": (r"AKIA[0-9A-Z]{16}", False),
            "AWS Secret Key": (r"aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]", True),
            "Generic API Key": (r"(api_key|apikey|secret_key|token)\s*=\s*['\"][A-Za-z0-9-_]{16,}['\"]", True),
            "Private Key": (r"-----BEGIN RSA PRIVATE KEY-----", False),
        }

        # Files to ignore
        ignore_dirs = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache'}

        # We try to use git grep first as it is faster and respects .gitignore
        git_path = shutil.which("git")
        if git_path and (self.project_dir / ".git").is_dir():
            for name, (pattern, case_insensitive) in patterns.items():
                try:
                    # -I: ignore binary files
                    # -n: line number
                    # -E: extended regex
                    cmd = [git_path, "-C", str(self.project_dir), "grep", "-I", "-n", "-E"]
                    if case_insensitive:
                        cmd.append("-i")
                    cmd.append(pattern)

                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.splitlines():
                            parts = line.split(":", 2)
                            if len(parts) >= 3:
                                file_path, line_num, content = parts[0], parts[1], parts[2]
                                findings.append({
                                    "type": "Secret",
                                    "issue_text": f"Potential {name} found",
                                    "filename": file_path,
                                    "line_number": int(line_num),
                                    "code": content.strip(),
                                    "severity": "HIGH"
                                })
                except Exception:
                    pass # Fallback to os.walk if git fails
        else:
            # Fallback to os.walk
            for root, dirs, files in os.walk(self.project_dir):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix in ['.py', '.js', '.ts', '.env', '.json', '.yaml', '.yml', '.txt']:
                        try:
                            content = file_path.read_text(errors='ignore')
                            for name, (pattern, case_insensitive) in patterns.items():
                                flags = re.IGNORECASE if case_insensitive else 0
                                for i, line in enumerate(content.splitlines()):
                                    if re.search(pattern, line, flags):
                                        findings.append({
                                            "type": "Secret",
                                            "issue_text": f"Potential {name} found",
                                            "filename": str(file_path.relative_to(self.project_dir)),
                                            "line_number": i + 1,
                                            "code": line.strip(),
                                            "severity": "HIGH"
                                        })
                        except Exception:
                            pass

        return findings

    def generate_report(self, bandit_findings: List[Dict], secret_findings: List[Dict]) -> str:
        lines = ["# 🛡️ Security Audit Report", ""]

        all_findings = bandit_findings + secret_findings

        # Helper to normalize severity
        def get_severity(f):
            return f.get('issue_severity', f.get('severity', 'LOW')).upper()

        # Separate by severity
        high = [f for f in all_findings if get_severity(f) == 'HIGH']
        medium = [f for f in all_findings if get_severity(f) == 'MEDIUM']
        low = [f for f in all_findings if get_severity(f) == 'LOW']

        lines.append(f"**Summary:**")
        lines.append(f"- 🔴 High Severity: {len(high)}")
        lines.append(f"- 🟡 Medium Severity: {len(medium)}")
        lines.append(f"- 🟢 Low Severity: {len(low)}")
        lines.append("")

        def format_finding(f):
            severity = get_severity(f)
            icon = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🟢"
            filename = f.get('filename')
            line = f.get('line_number')
            text = f.get('issue_text')

            # Mask secret if it looks like one
            code = f.get('code', '').strip()
            if "key" in text.lower() or "token" in text.lower() or "secret" in text.lower():
                 # Simple masking logic: keep first 4 and last 4 chars if length > 8
                 if len(code) > 8:
                     # Attempt to identify the secret part specifically if possible,
                     # but for now, we'll just mask the whole code snippet partially
                     # actually, let's look for quoted strings
                     code = re.sub(r"(['\"])(.*?)(['\"])", r"\1***\3", code)

            return f"### {icon} {text}\n- **File:** `{filename}:{line}`\n- **Severity:** {severity}\n- **Code:** `{code}`\n"

        if high:
            lines.append("## High Severity Issues")
            for f in high:
                lines.append(format_finding(f))

        if medium:
            lines.append("## Medium Severity Issues")
            for f in medium:
                lines.append(format_finding(f))

        if low:
            lines.append("## Low Severity Issues")
            for f in low:
                lines.append(format_finding(f))

        if not all_findings:
            lines.append("✅ No security issues found!")

        return "\n".join(lines)
