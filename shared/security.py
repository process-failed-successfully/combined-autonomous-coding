import json
import subprocess
import shutil
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from shared.logger import setup_logger

logger, _ = setup_logger(name="security")

@dataclass
class SecurityFinding:
    severity: str
    confidence: str
    file: str
    line: int
    issue_text: str
    code: str
    more_info: str

class SecurityAuditor:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def run_bandit(self, severity: str = "MEDIUM", confidence: str = "MEDIUM", format: str = "txt") -> Dict[str, Any]:
        """
        Runs bandit on the project directory.
        Severity: LOW, MEDIUM, HIGH
        Confidence: LOW, MEDIUM, HIGH
        """
        bandit_path = shutil.which("bandit")
        if not bandit_path:
            return {"error": "Bandit is not installed. Please install it via 'pip install bandit'."}

        # Map string levels to bandit flags if needed, but bandit uses -l (low), -ll (medium), -lll (high)
        # Actually, simpler to use --severity-level {low,medium,high}

        cmd = [
            bandit_path,
            "-r", str(self.project_dir),
            "-f", "json", # Always parse JSON internally for better handling
            "--severity-level", severity.lower(),
            "--confidence-level", confidence.lower(),
            "--exclude", ".venv,venv,tests,node_modules"
        ]

        # Load baseline if exists
        baseline_path = self.project_dir / "bandit_baseline.json"
        if baseline_path.exists():
            cmd.extend(["-b", str(baseline_path)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Bandit returns 1 if issues found, 0 if none.

            try:
                data = json.loads(result.stdout)
                return data
            except json.JSONDecodeError:
                return {"error": "Failed to parse bandit output", "raw_output": result.stdout}

        except Exception as e:
            return {"error": str(e)}

    def check_secrets(self) -> List[Dict[str, Any]]:
        """
        Basic regex-based secret scanning.
        """
        # This is a simplified check. In a real scenario, use truffleHog or similar.
        findings = []
        import re

        patterns = {
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "Generic Private Key": r"-----BEGIN (RSA|DSA|EC|PGP|OPENSSH) PRIVATE KEY-----",
            "GitHub Token": r"gh[pous]_[a-zA-Z0-9]{36,255}",
            "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})?",
            "Stripe API Key": r"sk_live_[0-9a-zA-Z]{24}",
        }

        # Walk files, excluding ignored
        ignored_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".agent_trash", ".agent_archives"}

        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]

            for filename in files:
                file_path = Path(root) / filename
                if file_path.suffix in [".pyc", ".so", ".o", ".db", ".sqlite"]:
                    continue

                # Skip large files
                if file_path.stat().st_size > 1024 * 1024: # 1MB
                    continue

                try:
                    content = file_path.read_text(errors="ignore")
                    for name, pattern in patterns.items():
                        if re.search(pattern, content):
                            findings.append({
                                "type": name,
                                "file": str(file_path.relative_to(self.project_dir)),
                                "severity": "HIGH"
                            })
                except Exception:
                    pass

        return findings

    def generate_report(self, bandit_results: Dict[str, Any], secret_findings: List[Dict[str, Any]]) -> str:
        report = []
        report.append("--- Security Audit Report ---")

        # Bandit Section
        if "error" in bandit_results:
             report.append(f"❌ Static Analysis Error: {bandit_results['error']}")
        else:
            results = bandit_results.get("results", [])
            metrics = bandit_results.get("metrics", {})

            total_issues = len(results)
            report.append(f"\n[Static Analysis (Bandit)]")
            report.append(f"  Scanned Files: {len(metrics)}")
            report.append(f"  Total Issues: {total_issues}")

            if total_issues == 0:
                report.append("  ✅ No static analysis issues found.")
            else:
                for issue in results:
                    report.append(f"\n  ⚠️  [{issue['test_id']}] {issue['issue_text']}")
                    report.append(f"      Severity: {issue['issue_severity']} | Confidence: {issue['issue_confidence']}")
                    report.append(f"      File: {issue['filename']}:{issue['line_number']}")
                    report.append(f"      More Info: {issue['more_info']}")

        # Secrets Section
        report.append(f"\n[Secret Scanning]")
        if not secret_findings:
            report.append("  ✅ No hardcoded secrets detected.")
        else:
            for finding in secret_findings:
                report.append(f"  🚨 Potential {finding['type']} in {finding['file']}")

        return "\n".join(report)
