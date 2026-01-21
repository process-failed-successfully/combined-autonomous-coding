import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

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
        lint_score = 20 if lint_res["passed"] else 10 # Partial credit? Or 0. Let's say 0 if failed.
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
        if self.score >= 90: self.grade = "A"
        elif self.score >= 80: self.grade = "B"
        elif self.score >= 70: self.grade = "C"
        elif self.score >= 60: self.grade = "D"
        else: self.grade = "F"

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
        print("\n" + "="*40)
        print(f"  PROJECT HEALTH REPORT: {self.grade} ({self.score:.0f}/100)")
        print("="*40)

        # Breakdown
        print(f"\nBreakdown:")
        print(f"  Tests:        {self.metrics['test_score']}/30")
        print(f"  Linting:      {self.metrics['lint_score']}/20")
        print(f"  Complexity:   {self.metrics['complexity_score']}/20")
        print(f"  Security:     {self.metrics['security_score']}/20")
        print(f"  Dependencies: {self.metrics['dependency_score']}/10")

        if self.issues:
            print(f"\n⚠️  Key Issues:")
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

def run_health_check(project_dir: Path):
    """Entry point for the health command."""
    calc = HealthCalculator(project_dir)
    calc.calculate()
    calc.print_report()
