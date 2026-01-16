import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any

class SecurityAuditor:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def run_audit(self, severity_level: str = "LOW") -> Dict[str, Any]:
        """
        Runs bandit on the project directory and returns the results.
        """
        bandit_path = shutil.which("bandit")
        if not bandit_path:
            return {"error": "Bandit is not installed. Please install it using 'pip install bandit'."}

        # Map severity level to bandit flags
        # We use --severity-level which accepts {low, medium, high} (case-sensitive, lowercase)
        # -l / -ll / -lll can be ambiguous depending on the bandit version and argument parsing
        level_arg = "low"
        if severity_level.upper() == "MEDIUM":
            level_arg = "medium"
        elif severity_level.upper() == "HIGH":
            level_arg = "high"

        # Construct command
        # We use -f json to get structured output
        # We also exclude .venv, venv, tests, and build directories by default to speed up and reduce noise
        cmd = [
            bandit_path,
            "-r", str(self.project_dir),
            "-f", "json",
            "--severity-level", level_arg,
            "-x", ".venv,venv,tests,build,.git,__pycache__"
        ]

        try:
            # Bandit returns exit code 1 if issues are found, which causes CalledProcessError
            # So we don't check=True immediately
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Bandit exit codes:
            # 0: No issues found
            # 1: Issues found
            # 2: Error occurred

            if result.returncode == 2:
                return {"error": f"Bandit encountered an error: {result.stderr}"}

            try:
                data = json.loads(result.stdout)
                return data
            except json.JSONDecodeError:
                 return {"error": f"Failed to parse Bandit output: {result.stdout}"}

        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}

    def generate_report(self, results: Dict[str, Any], format_type: str = "txt") -> str:
        """
        Generates a human-readable report from the audit results.
        """
        if "error" in results:
            return f"❌ Security Audit Failed: {results['error']}"

        if format_type == "json":
            return json.dumps(results, indent=2)

        # Text format
        report = []
        report.append("=== Security Audit Report ===")
        report.append(f"Generated at: {results.get('generated_time', 'Unknown')}")

        metrics = results.get("metrics", {})
        if metrics:
             report.append("\n--- Metrics ---")
             total_loc = sum(m.get('loc', 0) for m in metrics.values())
             report.append(f"Total Lines of Code Scanned: {total_loc}")

        issues = results.get("results", [])
        if not issues:
            report.append("\n✅ No security issues found!")
            return "\n".join(report)

        report.append(f"\nFound {len(issues)} security issue(s):")

        for i, issue in enumerate(issues, 1):
            severity = issue.get("issue_severity", "UNKNOWN")
            confidence = issue.get("issue_confidence", "UNKNOWN")
            filename = issue.get("filename", "unknown")
            line_no = issue.get("line_number", "?")
            code = issue.get("code", "").strip()
            text = issue.get("issue_text", "")
            test_id = issue.get("test_id", "")

            # Make path relative if possible
            try:
                rel_path = Path(filename).relative_to(self.project_dir)
            except ValueError:
                rel_path = filename

            icon = "🔴" if severity == "HIGH" else "🟠" if severity == "MEDIUM" else "🟡"

            report.append(f"\n{i}. [{icon} {severity}] {text}")
            report.append(f"   File: {rel_path}:{line_no}")
            report.append(f"   Confidence: {confidence}")
            if code:
                report.append(f"   Code: `{code}`")

            suggestion = self._get_fix_suggestion(test_id)
            if suggestion:
                report.append(f"   💡 Suggestion: {suggestion}")

        return "\n".join(report)

    def _get_fix_suggestion(self, test_id: str) -> str:
        """
        Returns a fix suggestion for a given Bandit test ID.
        """
        suggestions = {
            "B101": "Remove 'assert' statements from production code. Use proper error handling (raise Exception) or validation logic.",
            "B102": "Avoid using 'exec'. It can execute arbitrary code. Refactor to use standard language constructs.",
            "B103": "Check file permissions. Avoid setting 'chmod 777'. Use restricted permissions (e.g., 600 or 644).",
            "B104": "Avoid binding to all interfaces (0.0.0.0). Bind to a specific interface or localhost (127.0.0.1) if possible.",
            "B105": "Possible hardcoded password. Store secrets in environment variables or a secure vault.",
            "B106": "Possible hardcoded password in function argument. Use environment variables.",
            "B107": "Possible hardcoded password in default argument. Use environment variables.",
            "B108": "Avoid hardcoded '/tmp' paths. Use 'tempfile' module for secure temporary file creation.",
            "B110": "Avoid 'pass' in except blocks. Log the error or handle it explicitly.",
            "B112": "Avoid 'continue' in except blocks. Log the error or handle it explicitly.",
            "B113": "Requests call without timeout. Always add a 'timeout' argument to avoid hanging indefinitely.",
            "B301": "Pickle is insecure. Use JSON or another safe serialization format if the data source is untrusted.",
            "B303": "MD5 is insecure for cryptography. Use SHA256 or stronger (hashlib.sha256).",
            "B307": "Avoid using 'eval'. It can execute arbitrary code. Use 'ast.literal_eval' for safe evaluation of literals.",
            "B310": "Audit URL opening. Ensure the URL scheme is whitelisted (e.g., http, https) and inputs are validated.",
            "B311": "Standard pseudo-random generators are not suitable for security/crypto. Use 'secrets' module.",
            "B324": "Use of weak hashing algorithm. Use 'usedforsecurity=False' if not for security, or upgrade to SHA256+.",
            "B404": "Subprocess module usage detected. Ensure arguments are validated and 'shell=True' is avoided.",
            "B501": "Certificate validation disabled (verify=False). Enable certificate verification for HTTPS requests.",
            "B506": "Unsafe YAML load. Use 'yaml.safe_load()' instead of 'yaml.load()'.",
            "B602": "subprocess call with shell=True. Pass arguments as a list and set shell=False to prevent shell injection.",
            "B603": "subprocess call - ensure trusted input. Validate all inputs before passing to subprocess.",
            "B607": "Start process with partial path. Use absolute paths to executables.",
            "B608": "SQL injection risk. Use parameterized queries (e.g., '?' or '%s') instead of string formatting.",
        }
        return suggestions.get(test_id, "")
