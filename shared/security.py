import subprocess
import json
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class SecurityAuditor:
    def __init__(self):
        self.secret_patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "Generic API Key": r"(api_key|apikey|secret|token)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
            "Private Key": r"-----BEGIN PRIVATE KEY-----",
        }

    def run_bandit(self, project_dir: Path, severity: str = "medium") -> Dict[str, Any]:
        """Runs bandit security scan on the project directory."""
        try:
            # -f json to get JSON output
            # -r to recursive
            # -ll for severity (l=low, ll=medium, lll=high) - mapping to be done

            level_map = {"low": "l", "medium": "ll", "high": "lll"}
            severity_flag = f"-{level_map.get(severity, 'll')}"

            cmd = ["bandit", "-f", "json", "-r", str(project_dir), severity_flag]

            # Use exclude list similar to run_tests.sh
            cmd.extend(["-x", ".venv,venv,build,tests,.git"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            # Bandit returns exit code 1 if issues are found, which is fine.
            # We want the stdout.
            if result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse bandit output", "raw_output": result.stdout}
            return {"results": [], "metrics": {}}

        except FileNotFoundError:
             return {"error": "Bandit command not found. Please install it with 'pip install bandit'."}
        except Exception as e:
            return {"error": str(e)}

    def scan_secrets(self, project_dir: Path) -> List[Dict[str, Any]]:
        """Scans for potential hardcoded secrets."""
        findings = []

        # Use git ls-files if available to respect gitignore, otherwise os.walk
        git_files = self._get_git_files(project_dir)

        files_to_scan = []
        if git_files:
            files_to_scan = [project_dir / f for f in git_files]
        else:
            for root, _, files in os.walk(project_dir):
                if ".git" in root or ".venv" in root or "venv" in root or "__pycache__" in root:
                    continue
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.json', '.yaml', '.yml', '.md', '.txt', '.sh')):
                        files_to_scan.append(Path(root) / file)

        for file_path in files_to_scan:
            try:
                if not file_path.exists() or not file_path.is_file():
                    continue

                # Skip binary files
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue

                for line_num, line in enumerate(content.splitlines(), 1):
                    for name, pattern in self.secret_patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            # Mask the secret for report
                            match = re.search(pattern, line, re.IGNORECASE)
                            matched_text = match.group(0)
                            masked = matched_text[:4] + "*" * (len(matched_text) - 8) + matched_text[-4:] if len(matched_text) > 8 else "****"

                            findings.append({
                                "type": "Secret",
                                "issue_text": f"Potential {name} found",
                                "filename": str(file_path.relative_to(project_dir)),
                                "line_number": line_num,
                                "code": line.strip(),
                                "severity": "HIGH"
                            })
            except Exception:
                pass # safely ignore errors reading specific files

        return findings

    def _get_git_files(self, project_dir: Path) -> Optional[List[str]]:
        try:
            result = subprocess.run(
                ["git", "-C", str(project_dir), "ls-files"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.splitlines()
        except Exception:
            pass
        return None

    def audit(self, project_dir: Path, scan_type: str = "all", severity: str = "medium") -> Dict[str, Any]:
        """Runs the specified security checks."""
        report = {
            "summary": {"score": 100, "issues": 0},
            "findings": []
        }

        # 1. Bandit Scan
        if scan_type in ["all", "bandit"]:
            bandit_results = self.run_bandit(project_dir, severity)
            if "results" in bandit_results:
                for issue in bandit_results["results"]:
                    report["findings"].append({
                        "type": "Bandit",
                        "tool": "bandit",
                        "issue_text": issue.get("issue_text"),
                        "filename": issue.get("filename"),
                        "line_number": issue.get("line_number"),
                        "severity": issue.get("issue_severity"),
                        "confidence": issue.get("issue_confidence"),
                        "code": issue.get("code"),
                        "more_info": issue.get("more_info")
                    })
            elif "error" in bandit_results:
                report["errors"] = bandit_results["error"]

        # 2. Secret Scan
        if scan_type in ["all", "secrets"]:
            secret_findings = self.scan_secrets(project_dir)
            report["findings"].extend(secret_findings)

        report["summary"]["issues"] = len(report["findings"])
        # Basic scoring: deduct 10 for High, 5 for Medium, 1 for Low
        deductions = 0
        for finding in report["findings"]:
            sev = (finding.get("severity") or "LOW").upper()
            if sev == "HIGH": deductions += 10
            elif sev == "MEDIUM": deductions += 5
            else: deductions += 1

        report["summary"]["score"] = max(0, 100 - deductions)

        return report
