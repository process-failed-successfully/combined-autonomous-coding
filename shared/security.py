import os
import re
import subprocess  # nosec
import shutil
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

class SecurityAuditor:
    """
    Audits the codebase for security issues including secrets,
    SAST vulnerabilities, and dependency checks.
    """

    SECRET_PATTERNS = {
        "AWS Access Key": r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "AWS Secret Key": r"(?i)aws_secret_access_key['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9\/+=]{40}['\"]?",
        "Private Key": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
        "Generic API Key": r"(?i)(api_key|apikey|secret|token|password|passwd)['\"]?\s*[:=]\s*['\"]?[a-zA-Z0-9\-_]{16,}['\"]?",
    }

    DANGEROUS_PATTERNS = {
        "Dangerous Function (eval)": r"\beval\(",
        "Dangerous Function (exec)": r"\bexec\(",
        "Dangerous Function (pickle.load)": r"\bpickle\.load\(",
        "Subprocess with shell=True": r"subprocess\.(call|run|Popen).*shell\s*=\s*True",
        "Hardcoded Temp Path": r"\/tmp\/",
    }

    # Files/Dirs to ignore during secret scan
    IGNORE_DIRS = {
        ".git", "__pycache__", ".venv", "venv", "node_modules",
        ".idea", ".vscode", "dist", "build", ".agent_trash", ".agent_archives", "tests"
    }
    IGNORE_EXTENSIONS = {
        ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe",
        ".bin", ".pkl", ".png", ".jpg", ".jpeg", ".gif", ".ico",
        ".pdf", ".zip", ".tar", ".gz", ".7z", ".db", ".sqlite"
    }

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def _calculate_entropy(self, data: str) -> float:
        """Calculates the Shannon entropy of a string."""
        if not data:
            return 0.0
        entropy = 0.0
        for x in range(256):
            p_x = float(data.count(chr(x))) / len(data)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy

    def scan_secrets(self) -> List[Dict[str, Any]]:
        """Scans the project for hardcoded secrets."""
        findings = []

        for root, dirs, files in os.walk(self.project_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in self.IGNORE_EXTENSIONS:
                    continue

                # Check if path contains ignored keyword
                if any(ignored in file_path.parts for ignored in self.IGNORE_DIRS):
                    continue

                try:
                    # Skip files larger than 1MB to avoid performance issues
                    if file_path.stat().st_size > 1024 * 1024:
                        continue

                    # Read file content
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                    except Exception:
                        continue  # nosec

                    for name, pattern in self.SECRET_PATTERNS.items():
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            # Context extraction (simple)
                            start = max(0, match.start() - 20)
                            end = min(len(content), match.end() + 20)
                            snippet = content[start:end].replace('\n', ' ')

                            # Mask the secret in the snippet for display
                            match_str = match.group(0)

                            # Additional validation for "Generic API Key" to reduce false positives
                            if name == "Generic API Key":
                                # Extract value part
                                parts = re.split(r"[:=]\s*", match_str, 1)
                                if len(parts) > 1:
                                    value = parts[1].strip("'\"")
                                    # Ignore if value looks like a variable reference or placeholder
                                    if value.isupper() or "{" in value or "YOUR_" in value or "mock" in value.lower():
                                        continue

                                    # Entropy check
                                    entropy = self._calculate_entropy(value)
                                    if entropy < 3.0: # Arbitrary threshold, typical random keys have high entropy
                                        continue

                            masked_match = match_str[:4] + "***" + match_str[-4:] if len(match_str) > 8 else "***"
                            snippet = snippet.replace(match_str, masked_match)

                            findings.append({
                                "type": "secret",
                                "severity": "HIGH",
                                "description": f"Potential {name} found",
                                "file": str(file_path.relative_to(self.project_dir)),
                                "line": content[:match.start()].count('\n') + 1,
                                "snippet": snippet
                            })

                    # Scan for dangerous patterns
                    for name, pattern in self.DANGEROUS_PATTERNS.items():
                         matches = re.finditer(pattern, content)
                         for match in matches:
                            start = max(0, match.start() - 30)
                            end = min(len(content), match.end() + 30)
                            snippet = content[start:end].replace('\n', ' ')

                            findings.append({
                                "type": "dangerous_pattern",
                                "severity": "MEDIUM",
                                "description": f"{name} detected",
                                "file": str(file_path.relative_to(self.project_dir)),
                                "line": content[:match.start()].count('\n') + 1,
                                "snippet": snippet.strip()
                            })

                except Exception as e:
                    # Log error or skip file
                    continue  # nosec

        return findings

    def run_sast(self, severity: str = "medium") -> List[Dict[str, Any]]:
        """Runs Static Application Security Testing (Bandit for Python)."""
        findings = []

        # Check for Python
        if (self.project_dir / "requirements.txt").exists() or \
           (self.project_dir / "pyproject.toml").exists() or \
           list(self.project_dir.glob("*.py")):

            bandit_path = shutil.which("bandit")
            if bandit_path:
                try:
                    # Map severity to bandit args
                    severity_arg = "-ll" # Default low (shows everything)
                    if severity == "medium":
                        severity_arg = "-ll" # Bandit's severity flags are weird. -l is low, -ll is medium, -lll is high?
                        # Actually:
                        # -l: Report only issues of a given severity level or higher. (LOW)
                        # -ll: (MEDIUM)
                        # -lll: (HIGH)
                        pass

                    if severity == "low":
                        severity_arg = "-l"
                    elif severity == "medium":
                        severity_arg = "-ll"
                    elif severity == "high":
                        severity_arg = "-lll"

                    # Run bandit
                    # Recursive, JSON output, quiet
                    cmd = [
                        bandit_path,
                        "-r", str(self.project_dir),
                        "-f", "json",
                        "--quiet",
                        severity_arg,
                        # Exclude some common directories
                        "-x", ".venv,venv,tests,node_modules"
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True)  # nosec

                    # Bandit returns 1 if issues are found, which is fine
                    if result.stdout.strip():
                        try:
                            data = json.loads(result.stdout)
                            for result in data.get('results', []):
                                findings.append({
                                    "type": "sast",
                                    "tool": "bandit",
                                    "severity": result.get('issue_severity'),
                                    "description": result.get('issue_text'),
                                    "file": result.get('filename'),
                                    "line": result.get('line_number'),
                                    "snippet": result.get('code', '').strip()
                                })
                        except json.JSONDecodeError:
                            pass
                except Exception as e:
                    print(f"Error running bandit: {e}")
            else:
                findings.append({
                    "type": "warning",
                    "severity": "LOW",
                    "description": "Bandit not found. Skipping Python SAST scan.",
                    "file": "N/A",
                    "line": 0
                })

        return findings

    def run_dependency_check(self) -> List[Dict[str, Any]]:
        """Runs dependency checks (npm audit for Node)."""
        findings = []

        # Node.js
        if (self.project_dir / "package.json").exists() and shutil.which("npm"):
            try:
                cmd = ["npm", "audit", "--json"]
                result = subprocess.run(cmd, cwd=self.project_dir, capture_output=True, text=True)  # nosec
                # npm audit returns non-zero if vulnerabilities found

                if result.stdout.strip():
                    try:
                        data = json.loads(result.stdout)
                        if 'vulnerabilities' in data:
                            # v6 format (advisories) or v7+ format (vulnerabilities)
                            vulns = data.get('vulnerabilities', {})
                            for name, details in vulns.items():
                                # Recursive check might be needed for nested vulns, but let's keep it simple top-level
                                if isinstance(details, dict):
                                    findings.append({
                                        "type": "dependency",
                                        "tool": "npm audit",
                                        "severity": details.get('severity', 'unknown').upper(),
                                        "description": f"Vulnerability in {name}",
                                        "file": "package.json",
                                        "line": 0,
                                        "snippet": f"Upgrade {name}"
                                    })
                        elif 'advisories' in data:
                             # Older npm audit format
                             advisories = data.get('advisories', {})
                             for id, advisory in advisories.items():
                                 findings.append({
                                     "type": "dependency",
                                     "tool": "npm audit",
                                     "severity": advisory.get('severity', 'unknown').upper(),
                                     "description": advisory.get('title'),
                                     "file": "package.json",
                                     "line": 0,
                                     "snippet": f"Module: {advisory.get('module_name')}"
                                 })

                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                print(f"Error running npm audit: {e}")

        # Python (check for safety or pip-audit)
        # Note: safety is not in requirements, but if it exists we can use it.
        # For now, we skip Python deps check or add a placeholder.

        return findings

    def run_all(self, scan_type: str = "all", severity: str = "low") -> List[Dict[str, Any]]:
        all_findings = []

        if scan_type in ["all", "secrets"]:
            all_findings.extend(self.scan_secrets())

        if scan_type in ["all", "sast"]:
            all_findings.extend(self.run_sast(severity))

        if scan_type in ["all", "deps"]:
            all_findings.extend(self.run_dependency_check())

        return all_findings
