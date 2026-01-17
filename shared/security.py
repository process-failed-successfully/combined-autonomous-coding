import os
import re
import json
import shutil
import subprocess
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SecurityAuditor:
    """
    Audits the codebase for security vulnerabilities and secrets.
    Wraps 'bandit' for static analysis and implements custom secret scanning.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.bandit_path = shutil.which('bandit')

    def run_bandit(self, severity: str = 'LOW', output_file: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Runs bandit on the project directory.

        Args:
            severity: 'LOW', 'MEDIUM', or 'HIGH'
            output_file: Optional path to save the JSON report.

        Returns:
            A list of findings.
        """
        if not self.bandit_path:
            logger.error("Bandit executable not found. Please install bandit.")
            return []

        severity_flag = '-l' # Low
        if severity.upper() == 'MEDIUM':
            severity_flag = '-ll'
        elif severity.upper() == 'HIGH':
            severity_flag = '-lll'

        # Construct command
        # We use --quiet to avoid progress bars messing up JSON parsing if we captured it raw,
        # but we are using -f json, so it should be fine.
        cmd = [
            self.bandit_path,
            '-r', str(self.project_dir),
            '-f', 'json',
            severity_flag,
            '--quiet' # Suppress progress output
        ]

        # Exclude tests/ directory as per memory context
        cmd.extend(['-x', 'tests/'])

        if output_file:
            cmd.extend(['-o', str(output_file)])

        try:
            # Bandit returns exit code 1 if issues are found, which causes subprocess.check_output to fail.
            # We use run and check returncode manually, but we actually want the output regardless of exit code.
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )

            # Bandit exit codes: 0 = no issues, 1 = issues found, other = error
            if result.returncode not in [0, 1]:
                 logger.error(f"Bandit failed with exit code {result.returncode}: {result.stderr}")
                 return []

            # If output_file was specified, bandit wrote to it. We might read it back to return findings.
            if output_file:
                if output_file.exists():
                    try:
                        with open(output_file, 'r') as f:
                            data = json.load(f)
                            return data.get('results', [])
                    except json.JSONDecodeError:
                        logger.error("Failed to parse bandit JSON output from file.")
                        return []
                return []
            else:
                # Parse stdout
                try:
                    data = json.loads(result.stdout)
                    return data.get('results', [])
                except json.JSONDecodeError:
                    # If no issues found, bandit might not output JSON with --quiet?
                    # Actually with -f json it should always output JSON.
                    # Unless it crashed or produced empty output.
                    if not result.stdout.strip():
                        return []
                    logger.error(f"Failed to parse bandit JSON output: {result.stdout[:100]}...")
                    return []

        except Exception as e:
            logger.error(f"Error running bandit: {e}")
            return []

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """
        Scans the project for secrets using regex patterns.
        """
        findings = []

        # Regex Patterns
        # AWS Access Key ID: AKIA followed by 16 alphanumeric characters
        aws_access_key_pattern = re.compile(r'(AKIA[0-9A-Z]{16})')

        # AWS Secret Access Key: 40 chars base64-like
        # We look for typical assignment patterns to reduce false positives
        aws_secret_key_pattern = re.compile(r'(?i)(aws_secret_access_key|aws_secret_key)[\'"]?\s*[:=]\s*[\'"]?([A-Za-z0-9\/+=]{40})[\'"]?')

        # Private Keys
        private_key_pattern = re.compile(r'-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----')

        # Generic API Keys / Tokens
        # Look for "api_key", "token", "secret" followed by a string literal of 16+ chars
        # Quotes are mandatory for the value to match string literals
        generic_api_key_pattern = re.compile(r'(?i)(api_key|apikey|secret|token|password)[\'"]?\s*[:=]\s*[\'"]([A-Za-z0-9-_]{16,})[\'"]')

        files_to_scan = []
        exclude_dirs = {'.git', '.venv', '__pycache__', '.agent_trash', '.agent_archives', 'node_modules'}
        exclude_exts = {'.pyc', '.so', '.db', '.sqlite', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf'}

        for root, dirs, files in os.walk(self.project_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in exclude_exts:
                    continue
                files_to_scan.append(file_path)

        for file_path in files_to_scan:
            try:
                # Read file content. Use errors='ignore' to skip binary/encoding issues
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                lines = content.splitlines()
                for i, line in enumerate(lines):
                    # Check AWS Access Key
                    if match := aws_access_key_pattern.search(line):
                        findings.append({
                            'type': 'secret',
                            'issue_text': 'Found potential AWS Access Key ID',
                            'filename': str(file_path.relative_to(self.project_dir)),
                            'line_number': i + 1,
                            'line': line.strip(), # In a real report we might want to mask this
                            'severity': 'HIGH'
                        })

                    # Check AWS Secret Key
                    if match := aws_secret_key_pattern.search(line):
                        findings.append({
                            'type': 'secret',
                            'issue_text': 'Found potential AWS Secret Access Key',
                            'filename': str(file_path.relative_to(self.project_dir)),
                            'line_number': i + 1,
                            'line': line.strip(),
                            'severity': 'HIGH'
                        })

                    # Check Private Key
                    if match := private_key_pattern.search(line):
                        findings.append({
                            'type': 'secret',
                            'issue_text': 'Found Private Key block',
                            'filename': str(file_path.relative_to(self.project_dir)),
                            'line_number': i + 1,
                            'line': '-----BEGIN PRIVATE KEY----- ...',
                            'severity': 'HIGH'
                        })

                    # Check Generic API Key
                    if match := generic_api_key_pattern.search(line):
                        # Avoid common false positives like "token": "null" or "secret": "true"
                        value = match.group(2)
                        if value.lower() in ['true', 'false', 'null', 'undefined']:
                            continue

                        findings.append({
                            'type': 'secret',
                            'issue_text': f"Found potential secret ({match.group(1)})",
                            'filename': str(file_path.relative_to(self.project_dir)),
                            'line_number': i + 1,
                            'line': line.strip(),
                            'severity': 'MEDIUM' # Generic is lower confidence
                        })

            except Exception as e:
                logger.debug(f"Error reading file {file_path}: {e}")

        return findings

    def scan(self, scan_type: str = 'all', severity: str = 'LOW') -> List[Dict[str, Any]]:
        """
        Orchestrates the security scan.

        Args:
            scan_type: 'all', 'bandit', or 'secrets'
            severity: 'LOW', 'MEDIUM', 'HIGH' (for bandit)

        Returns:
            Combined list of findings.
        """
        results = []

        if scan_type in ['all', 'bandit']:
            logger.info("Running Bandit static analysis...")
            bandit_issues = self.run_bandit(severity=severity)
            # Normalize bandit issues
            for issue in bandit_issues:
                issue['type'] = 'bandit'
                issue['severity'] = issue.get('issue_severity', 'UNKNOWN').upper()
            results.extend(bandit_issues)

        if scan_type in ['all', 'secrets']:
            logger.info("Scanning for secrets...")
            secret_issues = self.scan_secrets()
            results.extend(secret_issues)

        # Sort by severity (HIGH > MEDIUM > LOW)
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'UNKNOWN': 3}
        results.sort(key=lambda x: severity_order.get(x.get('severity', 'UNKNOWN'), 4))

        return results

    @staticmethod
    def format_report(findings: List[Dict[str, Any]], output_format: str = 'text') -> str:
        """
        Formats the findings into a report string.
        """
        if output_format == 'json':
            return json.dumps(findings, indent=2)

        # Text Format
        if not findings:
            return "✅ No security issues found."

        report = [f"Found {len(findings)} security issue(s):"]

        for i, issue in enumerate(findings):
            severity = issue.get('severity', 'UNKNOWN')
            filename = issue.get('filename', 'unknown')
            line_no = issue.get('line_number', '?')
            text = issue.get('issue_text', issue.get('text', 'No description')) # Bandit uses 'issue_text'

            # Icon based on severity
            icon = "⚪"
            if severity == 'HIGH': icon = "🔴"
            elif severity == 'MEDIUM': icon = "🟡"
            elif severity == 'LOW': icon = "🔵"

            report.append(f"\n[{i+1}] {icon} {severity} - {text}")
            report.append(f"    File: {filename}:{line_no}")

            snippet = issue.get('code', issue.get('line'))
            if snippet:
                # Mask secrets in snippet
                masked_snippet = snippet.strip()
                if issue.get('type') == 'secret':
                    # Simple masking logic: mask match if possible, or just truncate
                    # For this implementation, we'll just say [REDACTED] if it looks sensitive
                    # But actually `scan_secrets` passes the raw line.
                    # Let's perform a simple mask of values in quotes for display
                    masked_snippet = re.sub(r'([\'"])(.*?)\1', r'\1********\1', masked_snippet)

                report.append(f"    Code: {masked_snippet}")

            if 'more_info' in issue:
                report.append(f"    Link: {issue['more_info']}")

        return "\n".join(report)
