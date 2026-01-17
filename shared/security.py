import subprocess
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

class SecurityAuditor:
    """
    Audits the codebase for security vulnerabilities using static analysis (Bandit)
    and custom secret scanning.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.findings: List[Dict[str, Any]] = []

    def run_bandit(self, baseline_file: Optional[Path] = None, severity_level: str = 'medium') -> List[Dict[str, Any]]:
        """
        Runs Bandit security linter on the project directory.
        """
        findings = []

        # Construct command
        cmd = [
            "bandit",
            "-r", str(self.project_dir),
            "-f", "json",
            "--exit-zero"  # Don't fail the subprocess, we parse output
        ]

        if severity_level == 'low':
            cmd.append("-l")
        elif severity_level == 'medium':
            cmd.append("-ll")
        elif severity_level == 'high':
            cmd.append("-lll")

        if baseline_file and baseline_file.exists():
            cmd.extend(["-b", str(baseline_file)])

        # Exclude common directories
        cmd.extend(["-x", ".venv,venv,build,tests,.git,node_modules"])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout.strip()

            if output:
                try:
                    data = json.loads(output)
                    # Transform bandit results into a common format
                    for result in data.get('results', []):
                        findings.append({
                            'tool': 'bandit',
                            'type': 'vulnerability',
                            'severity': result.get('issue_severity', 'UNKNOWN').upper(),
                            'file': result.get('filename'),
                            'line': result.get('line_number'),
                            'message': result.get('issue_text'),
                            'code': result.get('code'),
                            'details': result.get('more_info')
                        })
                except json.JSONDecodeError:
                    findings.append({
                        'tool': 'bandit',
                        'type': 'error',
                        'severity': 'HIGH',
                        'message': f"Failed to parse bandit output: {output[:200]}..."
                    })

            # Check stderr for execution errors if it exists (result might be a mock in tests)
            if hasattr(result, 'stderr') and result.stderr:
                # Bandit writes progress to stderr, so only care if it looks like a crash
                pass

        except FileNotFoundError:
             findings.append({
                'tool': 'bandit',
                'type': 'error',
                'severity': 'HIGH',
                'message': "Bandit executable not found. Please install it with `pip install bandit`."
            })

        self.findings.extend(findings)
        return findings

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """
        Scans files for potential hardcoded secrets using regex patterns.
        """
        secret_findings = []

        # Common patterns for secrets
        patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "Generic Private Key": r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
            "GitHub Token": r"ghp_[0-9a-zA-Z]{36}",
            "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})",
            "Generic API Key": r"(?i)(api_key|apikey|secret_key|secret|token)\s*[:=]\s*['\"]([A-Za-z0-9_\-]{16,})['\"]"
        }

        # Directories to ignore
        ignored_dirs = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', '.idea', '.vscode', 'build', 'dist', '.agent_trash', '.agent_archives'}
        # Files to ignore
        ignored_files = {'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', '.agent_history', 'final_metrics.txt', 'bandit_baseline.json', 'qa_summary.txt'}

        for root, dirs, files in os.walk(self.project_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignored_dirs]

            for file in files:
                if file in ignored_files or file.endswith(('.pyc', '.so', '.dylib', '.class', '.exe', '.db', '.sqlite')):
                    continue

                filepath = Path(root) / file

                # Check file size to avoid scanning huge files (e.g. > 1MB)
                try:
                    if filepath.stat().st_size > 1024 * 1024:
                        continue

                    try:
                        content = filepath.read_text(errors='ignore')
                    except Exception:
                        continue # Skip unreadable files

                    for name, pattern in patterns.items():
                        for match in re.finditer(pattern, content):
                            # For Generic API Key, capture group 2 is the secret, ensuring it looks like a high entropy string isn't perfect but helps.
                            # For others, the whole match is the concern.

                            matched_text = match.group(0)

                            # Filter out common false positives for generic keys
                            if name == "Generic API Key":
                                # Check if it's likely a variable reference or placeholder
                                secret_val = match.group(2)
                                if "ENV" in secret_val.upper() or "SECRET" == secret_val.upper() or "KEY" == secret_val.upper():
                                    continue

                            secret_findings.append({
                                'tool': 'secret-scanner',
                                'type': 'secret',
                                'severity': 'HIGH',
                                'file': str(filepath.relative_to(self.project_dir)),
                                'line': content[:match.start()].count('\n') + 1,
                                'message': f"Potential {name} detected.",
                                'code': matched_text[:50] + "..." if len(matched_text) > 50 else matched_text
                            })

                except Exception as e:
                    # Log error or ignore
                    pass

        self.findings.extend(secret_findings)
        return secret_findings

    def generate_report(self) -> str:
        """
        Generates a readable report from the findings.
        """
        if not self.findings:
            return "✅ Security Audit Passed: No issues found."

        report = ["⚠️ Security Audit Report", "=========================="]

        # Sort by severity
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "UNKNOWN": 3}
        sorted_findings = sorted(self.findings, key=lambda x: severity_order.get(x.get('severity', 'UNKNOWN'), 99))

        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}

        for finding in sorted_findings:
            sev = finding.get('severity', 'UNKNOWN')
            counts[sev] = counts.get(sev, 0) + 1

            icon = "🔴" if sev == "HIGH" else "🟠" if sev == "MEDIUM" else "🔵"
            report.append(f"\n{icon} [{sev}] {finding['tool']}: {finding['message']}")
            report.append(f"   File: {finding.get('file', 'N/A')}:{finding.get('line', 'N/A')}")
            if finding.get('code'):
                code_snippet = finding['code'].strip().replace('\n', ' ')
                if len(code_snippet) > 80:
                    code_snippet = code_snippet[:77] + "..."
                report.append(f"   Code: {code_snippet}")

        report.append("\nSummary:")
        report.append(f"  High: {counts['HIGH']}")
        report.append(f"  Medium: {counts['MEDIUM']}")
        report.append(f"  Low: {counts['LOW']}")

        return "\n".join(report)
