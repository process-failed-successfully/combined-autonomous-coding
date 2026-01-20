import sys
from pathlib import Path
from typing import Dict, Any, List

from shared.verify import run_lint, run_tests, run_security_scan
from shared.dependencies import DependencyAnalyzer
from shared.complexity import analyze_project_complexity

class HealthCalculator:
    """
    Calculates a comprehensive health score for the project.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir).resolve()
        self.scores: Dict[str, float] = {}
        self.details: Dict[str, Any] = {}
        self.max_scores = {
            "tests": 40,
            "lint": 20,
            "security": 20,
            "dependencies": 10,
            "complexity": 10
        }

    def run(self) -> Dict[str, Any]:
        """Runs all checks and returns the complete health report."""
        print(f"--- 🏥 Health Check: {self.project_dir.name} ---")

        self._check_tests()
        self._check_lint()
        self._check_security()
        self._check_dependencies()
        self._check_complexity()

        total_score = sum(self.scores.values())
        max_possible = sum(self.max_scores.values())

        # Determine grade
        grade = "F"
        if total_score >= 90: grade = "A+"
        elif total_score >= 80: grade = "A"
        elif total_score >= 70: grade = "B"
        elif total_score >= 60: grade = "C"
        elif total_score >= 50: grade = "D"

        return {
            "score": total_score,
            "max_score": max_possible,
            "grade": grade,
            "breakdown": self.scores,
            "details": self.details
        }

    def _check_tests(self):
        """Runs tests and assigns score."""
        print("  Running tests...", end="", flush=True)
        result = run_tests(self.project_dir)

        # Simple pass/fail for now, could be improved with coverage %
        passed = result["success"]

        # If passed, check coverage if available in stdout
        # stdout usually contains "TOTAL ... 85%"
        coverage = 0
        if passed and result["stdout"]:
            import re
            match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", result["stdout"])
            if match:
                coverage = int(match.group(1))

        score = 0
        if passed:
            # Base score for passing is 20
            score = 20
            # Additional 20 points for coverage
            score += (coverage / 100) * 20

        self.scores["tests"] = round(score, 1)
        self.details["tests"] = {
            "passed": passed,
            "coverage": coverage,
            "output": result["stdout"] if not passed else "Tests Passed"
        }
        print(f" Done ({self.scores['tests']}/{self.max_scores['tests']})")

    def _check_lint(self):
        """Runs lint and subtracts points for errors."""
        print("  Checking code style...", end="", flush=True)
        result = run_lint(self.project_dir)

        # Parse stdout for error count
        # flake8 --statistics output looks like: "count error_code message"
        error_count = 0
        output = result["stdout"] or ""
        for line in output.splitlines():
            # Only count actual errors reported by --statistics usually at end
            # or count lines that look like "path:line:col: code msg"
            if ": E" in line or ": F" in line: # Errors and failures
                error_count += 1

        # Deduct 1 point per error, max deduction 20
        score = max(0, self.max_scores["lint"] - error_count)

        self.scores["lint"] = score
        self.details["lint"] = {
            "issues": error_count,
            "output": output[:500] + "..." if len(output) > 500 else output
        }
        print(f" Done ({self.scores['lint']}/{self.max_scores['lint']})")

    def _check_security(self):
        """Runs security scan and subtracts points for issues."""
        print("  Scanning security...", end="", flush=True)
        result = run_security_scan(self.project_dir)

        # Parse stdout for issue count from bandit
        # Bandit output contains "Total issues (by severity):"
        # High: 0, Medium: 0, Low: 0
        high = 0
        medium = 0
        low = 0

        output = result["stdout"] or ""
        import re

        # Try to find CSV or JSON output if verify.py uses custom format,
        # but verify.py uses default text or custom format depending on flags.
        # Let's look for "Sev: High" or similar if text format

        # Bandit text summary:
        # High: 0
        # Medium: 0
        # Low: 0

        h_match = re.search(r"High: (\d+)", output)
        if h_match: high = int(h_match.group(1))

        m_match = re.search(r"Medium: (\d+)", output)
        if m_match: medium = int(m_match.group(1))

        l_match = re.search(r"Low: (\d+)", output)
        if l_match: low = int(l_match.group(1))

        # Weighted deduction
        deduction = (high * 10) + (medium * 3) + (low * 1)
        score = max(0, self.max_scores["security"] - deduction)

        self.scores["security"] = score
        self.details["security"] = {
            "high": high,
            "medium": medium,
            "low": low
        }
        print(f" Done ({self.scores['security']}/{self.max_scores['security']})")

    def _check_dependencies(self):
        """Checks for outdated dependencies."""
        print("  Checking dependencies...", end="", flush=True)
        analyzer = DependencyAnalyzer(self.project_dir)
        data = analyzer.scan()
        data = analyzer.check_updates(data)

        outdated_count = 0
        for lang, files in data.items():
            for f in files:
                for dep in f.get("dependencies", []):
                    if dep.get("outdated"):
                        outdated_count += 1

        # Deduct 1 point per outdated dep
        score = max(0, self.max_scores["dependencies"] - outdated_count)

        self.scores["dependencies"] = score
        self.details["dependencies"] = {"outdated": outdated_count}
        print(f" Done ({self.scores['dependencies']}/{self.max_scores['dependencies']})")

    def _check_complexity(self):
        """Checks cyclomatic complexity."""
        print("  Analyzing complexity...", end="", flush=True)
        results = analyze_project_complexity(self.project_dir)

        if not results:
            self.scores["complexity"] = self.max_scores["complexity"]
            self.details["complexity"] = {"average": 0, "high_risk": 0}
            print(f" Done ({self.scores['complexity']}/{self.max_scores['complexity']})")
            return

        avg_complexity = sum(r["complexity"] for r in results) / len(results)
        high_risk_count = sum(1 for r in results if r["complexity"] > 10)

        # Scoring:
        # Full points if avg <= 5 and no high risk
        # Deduct based on average and high risk count

        score = self.max_scores["complexity"]
        if avg_complexity > 5:
            score -= (avg_complexity - 5) # Deduct 1 point per unit over 5

        score -= (high_risk_count * 2) # Deduct 2 points per high risk function

        self.scores["complexity"] = max(0, round(score, 1))
        self.details["complexity"] = {
            "average": round(avg_complexity, 1),
            "high_risk": high_risk_count
        }
        print(f" Done ({self.scores['complexity']}/{self.max_scores['complexity']})")

def run_health(project_dir: Path, json_output: bool = False):
    """Entry point for health check."""
    calc = HealthCalculator(project_dir)
    report = calc.run()

    if json_output:
        print(json.dumps(report, indent=2))
        return

    # Text Report
    print("\n" + "="*40)
    print(f"  PROJECT HEALTH REPORT")
    print("="*40)

    # Grade
    color = "\033[92m" # Green
    if report["score"] < 70: color = "\033[93m" # Yellow
    if report["score"] < 50: color = "\033[91m" # Red
    reset = "\033[0m"

    print(f"\nOverall Score: {color}{report['score']:.1f} / {report['max_score']}{reset}  (Grade: {report['grade']})")

    # Breakdown
    print("\n--- Breakdown ---")
    for category, score in report["breakdown"].items():
        max_score = calc.max_scores[category]
        bar_len = int((score / max_score) * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"{category.capitalize().ljust(15)} | {bar} | {score}/{max_score}")

    # Details
    print("\n--- Details ---")
    d = report["details"]

    # Tests
    print(f"Tests: {'✅ Passed' if d['tests']['passed'] else '❌ Failed'} (Coverage: {d['tests']['coverage']}%)")

    # Lint
    if d['lint']['issues'] > 0:
        print(f"Lint: Found {d['lint']['issues']} style issues.")
    else:
        print("Lint: Clean.")

    # Security
    sec = d['security']
    if sec['high'] or sec['medium'] or sec['low']:
        print(f"Security: Issues found - High: {sec['high']}, Med: {sec['medium']}, Low: {sec['low']}")
    else:
        print("Security: Clean.")

    # Dependencies
    if d['dependencies']['outdated'] > 0:
        print(f"Dependencies: {d['dependencies']['outdated']} packages are outdated.")
    else:
        print("Dependencies: Up to date.")

    # Complexity
    print(f"Complexity: Avg {d['complexity']['average']}, High Risk Functions: {d['complexity']['high_risk']}")

    print("\n" + "="*40)
