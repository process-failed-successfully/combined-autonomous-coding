from pathlib import Path
from typing import Dict, Any
import json
import html
from datetime import datetime

from shared.complexity import analyze_project_complexity
from shared.verify import run_tests, run_lint
from shared.security import SecurityAuditor
from shared.dependencies import DependencyAnalyzer

class HealthCalculator:
    """
    Calculates the project health score based on various metrics.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.metrics = {}
        self.score = 0.0
        self.grade = "F"
        self.issues = []
        self.timestamp = datetime.now()

    def run_check(self, check_type: str) -> Dict[str, Any]:
        """Runs a specific check and returns normalized results."""
        if check_type == "tests":
            # Run tests
            result = run_tests(self.project_dir, output_format="json")
            # Parse output or determine success from result object (which is mocked dict in shared/verify)
            # Actually run_tests returns a dict with success, stdout, stderr
            passed = result.get("success", False)
            return {"passed": passed, "raw": result}

        elif check_type == "lint":
            # Run lint
            result = run_lint(self.project_dir, output_format="json")
            passed = result.get("success", False)
            # Extract error count from stdout if possible?
            # Flake8 output usually has statistics at the end if configured
            return {"passed": passed, "raw": result}

        elif check_type == "complexity":
            # Run complexity analysis
            complexity_data = analyze_project_complexity(self.project_dir)
            if not complexity_data:
                return {"average": 0, "max": 0, "high_risk_count": 0}

            avg = sum(c["complexity"] for c in complexity_data) / len(complexity_data)
            max_c = max(c["complexity"] for c in complexity_data)
            high_risk = len([c for c in complexity_data if c["complexity"] > 10])

            return {
                "average": avg,
                "max": max_c,
                "high_risk_count": high_risk,
                "total_functions": len(complexity_data)
            }

        elif check_type == "security":
            # Run security scan
            auditor = SecurityAuditor(self.project_dir)
            findings = auditor.run_all(scan_type="all", severity="medium")
            high_sev = len([f for f in findings if f.get("severity", "").upper() == "HIGH"])
            med_sev = len([f for f in findings if f.get("severity", "").upper() == "MEDIUM"])
            return {"findings": findings, "high": high_sev, "medium": med_sev}

        elif check_type == "dependencies":
            analyzer = DependencyAnalyzer(self.project_dir)
            data = analyzer.scan()
            data = analyzer.check_updates(data)
            outdated_count = 0
            for lang, files in data.items():
                for file_info in files:
                    for dep in file_info.get("dependencies", []):
                        if dep.get("outdated"):
                            outdated_count += 1
            return {"outdated_count": outdated_count}

        return {}

    def calculate(self):
        """Runs all checks and calculates the final score."""
        print(f"--- Calculating Project Health for: {self.project_dir.name} ---")

        # 1. Tests (30 points)
        print("Running tests...")
        test_res = self.run_check("tests")
        test_score = 30 if test_res["passed"] else 0
        if not test_res["passed"]:
            self.issues.append("Tests failed.")

        # 2. Linting (20 points)
        print("Running linter...")
        lint_res = self.run_check("lint")
        lint_score = 20 if lint_res["passed"] else 10  # Partial credit? Or 0. Let's say 0 if failed.
        if not lint_res["passed"]:
            # Check if it was a total failure or just warnings
            lint_score = 0
            self.issues.append("Linting failed (code style issues).")

        # 3. Complexity (20 points)
        print("Analyzing complexity...")
        comp_res = self.run_check("complexity")
        comp_score = 20
        if comp_res.get("average", 0) > 10:
            comp_score -= 10
            self.issues.append(f"High average complexity ({comp_res['average']:.1f}).")
        if comp_res.get("high_risk_count", 0) > 0:
            penalty = min(10, comp_res["high_risk_count"] * 2)
            comp_score -= penalty
            self.issues.append(f"Found {comp_res['high_risk_count']} functions with high complexity.")
        comp_score = max(0, comp_score)

        # 4. Security (20 points)
        print("Scanning security...")
        sec_res = self.run_check("security")
        sec_score = 20
        if sec_res.get("high", 0) > 0:
            sec_score = 0 # automatic fail on security score if high sev
            self.issues.append(f"Found {sec_res['high']} HIGH severity security issues.")
        elif sec_res.get("medium", 0) > 0:
            penalty = min(10, sec_res["medium"] * 2)
            sec_score -= penalty
            self.issues.append(f"Found {sec_res['medium']} medium severity security issues.")
        sec_score = max(0, sec_score)

        # 5. Dependencies (10 points)
        print("Checking dependencies...")
        dep_res = self.run_check("dependencies")
        dep_score = 10
        if dep_res.get("outdated_count", 0) > 0:
            penalty = min(10, dep_res["outdated_count"] * 1)
            dep_score -= penalty
            self.issues.append(f"Found {dep_res['outdated_count']} outdated dependencies.")
        dep_score = max(0, dep_score)

        # Total
        self.score = test_score + lint_score + comp_score + sec_score + dep_score

        # Grading
        if self.score >= 90:
            self.grade = "A"
        elif self.score >= 80:
            self.grade = "B"
        elif self.score >= 70:
            self.grade = "C"
        elif self.score >= 60:
            self.grade = "D"
        else:
            self.grade = "F"

        self.metrics = {
            "test_score": test_score,
            "lint_score": lint_score,
            "complexity_score": comp_score,
            "security_score": sec_score,
            "dependency_score": dep_score,
            "complexity_data": comp_res,
            "security_data": sec_res,
            "dependency_data": dep_res
        }

    def print_report(self):
        """Prints a nice report."""
        print("\n" + "=" * 40)
        print(f"  PROJECT HEALTH REPORT: {self.grade} ({self.score:.0f}/100)")
        print("=" * 40)

        # Breakdown
        print("\nBreakdown:")
        print(f"  Tests:        {self.metrics['test_score']}/30")
        print(f"  Linting:      {self.metrics['lint_score']}/20")
        print(f"  Complexity:   {self.metrics['complexity_score']}/20")
        print(f"  Security:     {self.metrics['security_score']}/20")
        print(f"  Dependencies: {self.metrics['dependency_score']}/10")

        if self.issues:
            print("\n⚠️  Key Issues:")
            for issue in self.issues:
                print(f"  - {issue}")
        else:
            print("\n✅ No significant issues found.")

        print("\nRecommendations:")
        if self.metrics['test_score'] < 30:
            print("  - Fix failing tests or add more test coverage.")
        if self.metrics['lint_score'] < 20:
            print("  - Run 'verify --fix' to resolve linting issues.")
        if self.metrics['complexity_score'] < 20:
            print("  - Refactor complex functions (use 'polish' command).")
        if self.metrics['security_score'] < 20:
            print("  - Address security vulnerabilities (use 'security' command).")
        if self.metrics['dependency_score'] < 10:
            print("  - Update dependencies (use 'deps --update').")

        if self.score == 100:
            print("  - Great job! Keep it up.")

    def generate_json_report(self, output_path: Path):
        """Generates a JSON report."""
        report = {
            "project_name": self.project_dir.name,
            "timestamp": self.timestamp.isoformat(),
            "grade": self.grade,
            "score": self.score,
            "metrics": self.metrics,
            "issues": self.issues
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

    def generate_html_report(self, output_path: Path):
        """Generates an HTML report."""

        # Color coding for grade
        grade_color = "#e74c3c"  # Red (F)
        if self.grade == "A":
            grade_color = "#2ecc71"  # Green
        elif self.grade == "B":
            grade_color = "#3498db"  # Blue
        elif self.grade == "C":
            grade_color = "#f1c40f"  # Yellow
        elif self.grade == "D":
            grade_color = "#e67e22"  # Orange

        project_name = html.escape(self.project_dir.name)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Health Report - {project_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background: #f9f9f9; }}
        .container {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 20px; }}
        .grade-badge {{ background: {grade_color}; color: #fff; font-size: 3em; font-weight: bold; width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }}
        .score-info {{ text-align: right; }}
        .score-number {{ font-size: 2em; font-weight: bold; color: {grade_color}; }}
        .section {{ margin-bottom: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }}
        .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #bdc3c7; }}
        .metric-card.pass {{ border-left-color: #2ecc71; }}
        .metric-card.fail {{ border-left-color: #e74c3c; }}
        .metric-title {{ font-size: 0.9em; text-transform: uppercase; color: #7f8c8d; letter-spacing: 1px; }}
        .metric-value {{ font-size: 1.5em; font-weight: bold; }}
        .issues-list {{ background: #fff3cd; color: #856404; padding: 15px; border-radius: 6px; border: 1px solid #ffeeba; }}
        .issues-list ul {{ margin: 0; padding-left: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        .footer {{ text-align: center; font-size: 0.8em; color: #7f8c8d; margin-top: 40px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>Project Health Report</h1>
                <p>Project: <strong>{project_name}</strong></p>
                <p>Date: {self.timestamp.strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            <div class="grade-badge">{self.grade}</div>
        </div>

        <div class="score-info">
            Overall Score: <span class="score-number">{self.score:.0f}</span> / 100
        </div>

        <div class="section">
            <h2>Breakdown</h2>
            <div class="metric-grid">
                <div class="metric-card {"pass" if self.metrics["test_score"] == 30 else "fail"}">
                    <div class="metric-title">Tests</div>
                    <div class="metric-value">{self.metrics["test_score"]}/30</div>
                </div>
                <div class="metric-card {"pass" if self.metrics["lint_score"] >= 15 else "fail"}">
                    <div class="metric-title">Linting</div>
                    <div class="metric-value">{self.metrics["lint_score"]}/20</div>
                </div>
                <div class="metric-card {"pass" if self.metrics["complexity_score"] >= 15 else "fail"}">
                    <div class="metric-title">Complexity</div>
                    <div class="metric-value">{self.metrics["complexity_score"]}/20</div>
                </div>
                <div class="metric-card {"pass" if self.metrics["security_score"] >= 15 else "fail"}">
                    <div class="metric-title">Security</div>
                    <div class="metric-value">{self.metrics["security_score"]}/20</div>
                </div>
                <div class="metric-card {"pass" if self.metrics["dependency_score"] >= 8 else "fail"}">
                    <div class="metric-title">Dependencies</div>
                    <div class="metric-value">{self.metrics["dependency_score"]}/10</div>
                </div>
            </div>
        </div>

        {self._render_issues_section()}
        {self._render_details_section()}

        <div class="footer">
            Generated by Autonomous Coding Agent
        </div>
    </div>
</body>
</html>
"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _render_issues_section(self) -> str:
        if not self.issues:
            return """<div class="section"><h2>Key Issues</h2><p>✅ No significant issues found.</p></div>"""

        items = "".join([f"<li>{html.escape(str(issue))}</li>" for issue in self.issues])
        return f"""
        <div class="section">
            <h2>Key Issues</h2>
            <div class="issues-list">
                <ul>{items}</ul>
            </div>
        </div>
        """

    def _render_details_section(self) -> str:
        # Construct detailed tables if data is available
        details = ""

        # Security Findings
        findings = self.metrics.get("security_data", {}).get("findings", [])
        if findings:
            rows = ""
            for f in findings:
                ftype = html.escape(str(f.get('type', '')))
                sev = html.escape(str(f.get('severity', '')))
                desc = html.escape(str(f.get('description', '')))
                file = html.escape(str(f.get('file', '')))
                line = html.escape(str(f.get('line', '')))
                rows += f"<tr><td>{ftype}</td><td>{sev}</td><td>{desc}</td><td>{file}:{line}</td></tr>"

            details += f"""
            <h3>Security Findings</h3>
            <table>
                <thead><tr><th>Type</th><th>Severity</th><th>Description</th><th>Location</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            """

        return f"<div class=\"section\"><h2>Details</h2>{details if details else '<p>No detailed findings available.</p>'}</div>"


def run_health_check(project_dir: Path, output_format: str = "text", output_file: str = None):
    """Entry point for the health command."""
    calc = HealthCalculator(project_dir)
    calc.calculate()

    if output_format == "html":
        out_path = Path(output_file) if output_file else project_dir / "health_report.html"
        calc.generate_html_report(out_path)
        print(f"\n✅ HTML Report generated: {out_path}")
    elif output_format == "json":
        out_path = Path(output_file) if output_file else project_dir / "health_report.json"
        calc.generate_json_report(out_path)
        print(f"\n✅ JSON Report generated: {out_path}")
    else:
        calc.print_report()
        if output_file:
            # If user specifically asked for text output to a file
            # We redirect stdout or just write it. For now, let's keep it simple and just print to stdout
            # as print_report does. If they want file, they can pipe it or use json/html.
            print(f"Note: Text output is printed to console. Use --format html or json for file output.")
