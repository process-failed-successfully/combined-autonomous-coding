import os
import re
import subprocess
import shutil
import json
import math
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.dependencies import DependencyAnalyzer

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
            return 0
        entropy = 0
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
                        continue

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
                    continue

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

                    result = subprocess.run(cmd, capture_output=True, text=True)

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

    def _check_python_vulnerabilities(self, python_deps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Queries the OSV API (https://osv.dev) for Python vulnerabilities.
        """
        findings = []
        if not python_deps:
            return findings

        # Extract unique packages to query
        unique_pkgs = {}
        for file_info in python_deps:
            source = file_info["source"]
            for dep in file_info.get("dependencies", []):
                key = (dep["name"], dep.get("version"))
                if key not in unique_pkgs:
                    unique_pkgs[key] = []
                unique_pkgs[key].append(source)

        if not unique_pkgs:
            return findings

        # Construct batch query for OSV
        # Batching (1000 limit) - for now assuming < 1000 deps
        queries = []
        pkg_list = []
        for (name, version), sources in unique_pkgs.items():
            if not version:
                continue # Cannot check without version

            # Remove operators from version if present (e.g. ==, >=)
            clean_version = version.lstrip("=<>~")

            queries.append({
                "package": {
                    "name": name,
                    "ecosystem": "PyPI"
                },
                "version": clean_version
            })
            pkg_list.append(((name, version), sources))

        if not queries:
            return findings

        try:
            url = "https://api.osv.dev/v1/querybatch"
            response = requests.post(url, json={"queries": queries}, timeout=10)

            if response.status_code == 200:
                results = response.json().get("results", [])

                for i, result in enumerate(results):
                    vulns = result.get("vulns", [])
                    if vulns:
                        (pkg_name, pkg_ver), sources = pkg_list[i]
                        for vuln in vulns:
                            # Map to finding
                            summary = vuln.get("summary") or vuln.get("details", "No description")
                            if len(summary) > 200:
                                summary = summary[:200] + "..."

                            findings.append({
                                "type": "dependency",
                                "tool": "OSV (PyPI)",
                                "severity": "HIGH", # OSV doesn't always provide simple severity, assume high for now or parse CVSS
                                "description": f"{pkg_name} {pkg_ver}: {vuln['id']} - {summary}",
                                "file": ", ".join(sources),
                                "line": 0,
                                "snippet": f"Upgrade {pkg_name}",
                                "url": f"https://osv.dev/vulnerability/{vuln['id']}"
                            })

        except Exception as e:
            print(f"Error checking Python vulnerabilities: {e}")

        return findings

    def run_dependency_check(self) -> List[Dict[str, Any]]:
        """Runs dependency checks (npm audit for Node, OSV for Python)."""
        findings = []

        # Node.js
        if (self.project_dir / "package.json").exists() and shutil.which("npm"):
            try:
                cmd = ["npm", "audit", "--json"]
                result = subprocess.run(cmd, cwd=self.project_dir, capture_output=True, text=True)
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

        # Python (OSV Check)
        try:
            analyzer = DependencyAnalyzer(self.project_dir)
            deps = analyzer.scan()
            python_deps = deps.get("python", [])
            if python_deps:
                print("Checking Python dependencies against OSV database...")
                py_findings = self._check_python_vulnerabilities(python_deps)
                findings.extend(py_findings)
        except Exception as e:
            print(f"Error running Python dependency check: {e}")

        return findings

    def scan_git_history(self, depth: int = 100) -> List[Dict[str, Any]]:
        """Scans the git history for secrets."""
        findings = []

        if not shutil.which("git"):
            return []

        if not (self.project_dir / ".git").exists():
            return []

        try:
            # -p: generate diffs
            # -n {depth}: limit number of commits
            # --unified=0: 0 lines of context to reduce output size
            cmd = ["git", "log", "-p", f"-n{depth}", "--unified=0"]

            # Using errors='ignore' to handle potential binary data or encoding issues in history
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            current_commit = None
            current_author = None
            current_date = None
            current_file = None

            for line in result.stdout.splitlines():
                if line.startswith("commit "):
                    current_commit = line.split(" ")[1]
                    current_author = None  # Reset
                    current_date = None  # Reset
                    current_file = None  # Reset
                elif line.startswith("Author:"):
                    current_author = line.split(":", 1)[1].strip()
                elif line.startswith("Date:"):
                    current_date = line.split(":", 1)[1].strip()
                elif line.startswith("diff --git"):
                    # Attempt to extract filename from diff header
                    # Robust parsing is hard with just string splitting due to spaces
                    # A regex approach is safer: diff --git a/(.*) b/(.*)
                    match = re.search(r"^diff --git a/(.*) b/(.*)$", line)
                    if match:
                        current_file = match.group(2).strip()
                    else:
                        # Fallback: try to parse last part if regex fails
                        parts = line.split(" ")
                        if len(parts) >= 4:
                            current_file = parts[-1].lstrip("b/").strip()

                elif line.startswith("+++ b/"):
                    # Verify/update filename from the +++ line which is often present
                    current_file = line[6:].strip()

                # Check for added lines
                elif line.startswith("+") and not line.startswith("+++"):
                    if not current_commit or not current_file:
                        continue

                    # Ignore checks
                    file_path = Path(current_file)
                    if file_path.suffix in self.IGNORE_EXTENSIONS:
                        continue

                    # Check path components to avoid partial substring matches
                    # e.g. avoid ignoring "builder.py" just because "build" is ignored
                    if any(ignored in file_path.parts for ignored in self.IGNORE_DIRS):
                        continue

                    content = line[1:]  # strip the +

                    for name, pattern in self.SECRET_PATTERNS.items():
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            # Context extraction not really needed as we have the line
                            match_str = match.group(0)

                            # Entropy check for API keys
                            if name == "Generic API Key":
                                parts = re.split(r"[:=]\s*", match_str, 1)
                                if len(parts) > 1:
                                    value = parts[1].strip("'\"")
                                    if value.isupper() or "{" in value or "YOUR_" in value or "mock" in value.lower():
                                        continue
                                    if self._calculate_entropy(value) < 3.0:
                                        continue

                            masked_match = match_str[:4] + "***" + match_str[-4:] if len(match_str) > 8 else "***"
                            snippet = content.replace(match_str, masked_match)

                            findings.append({
                                "type": "secret_history",
                                "severity": "HIGH",
                                "description": f"Potential {name} in git history",
                                "file": current_file,
                                "line": 0,  # Line number hard to track in unified=0 diff without counting
                                "snippet": snippet.strip(),
                                "commit": current_commit,
                                "author": current_author,
                                "date": current_date
                            })

        except Exception as e:
            print(f"Error scanning git history: {e}")

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
