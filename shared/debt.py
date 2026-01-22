"""
Technical Debt Collector
========================

Aggregates various code quality metrics to provide a technical debt assessment.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import math

from shared.todos import scan_todos
from shared.complexity import analyze_project_complexity
from shared.duplication import find_duplicates
from shared.unused import UnusedCodeDetector

class DebtCollector:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def collect(self) -> Dict[str, Any]:
        """Collects metrics from various sources."""

        # 1. TODOs
        todos = scan_todos(self.project_dir)
        todo_metrics = {
            "count": len(todos),
            "items": todos
        }

        # 2. Complexity
        complexity_results = analyze_project_complexity(self.project_dir)
        total_complexity = sum(r["complexity"] for r in complexity_results)
        count_functions = len(complexity_results)

        high_risk = [r for r in complexity_results if r["complexity"] > 10]
        total_excess = sum(r["complexity"] - 10 for r in high_risk)

        complexity_metrics = {
            "count": count_functions,
            "average": (total_complexity / count_functions) if count_functions else 0,
            "max": max((r["complexity"] for r in complexity_results), default=0),
            "high_risk_count": len(high_risk),
            "total_excess": total_excess,
            "high_risk_items": sorted(high_risk, key=lambda x: x["complexity"], reverse=True)[:5]
        }

        # 3. Duplication
        duplicates = find_duplicates(self.project_dir, min_tokens=50)
        duplication_metrics = {
            "blocks": len(duplicates),
            "total_tokens": sum(d["token_count"] for d in duplicates),
            "items": duplicates[:5]
        }

        # 4. Unused Code
        unused_detector = UnusedCodeDetector(self.project_dir)
        unused_detector.scan()
        unused_items = unused_detector.get_unused_definitions()

        unused_metrics = {
            "count": len(unused_items),
            "items": unused_items[:5]
        }

        return {
            "todos": todo_metrics,
            "complexity": complexity_metrics,
            "duplication": duplication_metrics,
            "unused": unused_metrics
        }

    def calculate_score(self, metrics: Dict[str, Any]) -> Tuple[float, str]:
        """
        Calculates a debt score (higher is worse) and assigns a grade.

        Formula (Heuristic):
        - TODOs: 1 point each
        - Complexity: 5 points per high-risk function + 1 point per excess complexity unit
        - Duplication: 1 point per 10 tokens duplicated
        - Unused: 5 points per unused item
        """
        score = 0.0

        # TODOs
        score += metrics["todos"]["count"] * 1.0

        # Complexity
        score += metrics["complexity"]["high_risk_count"] * 5.0
        score += metrics["complexity"].get("total_excess", 0) * 1.0

        # Duplication
        score += metrics["duplication"]["total_tokens"] / 10.0

        # Unused
        score += metrics["unused"]["count"] * 5.0

        # Grading
        if score <= 50:
            grade = "A"
        elif score <= 150:
            grade = "B"
        elif score <= 300:
            grade = "C"
        elif score <= 500:
            grade = "D"
        else:
            grade = "F"

        return score, grade

def run_debt_report(project_dir: Path, json_output: bool = False):
    """Generates and prints the technical debt report."""
    collector = DebtCollector(project_dir)
    print(f"Analyzing technical debt in {project_dir}...")
    print("(This may take a moment as we scan for complexity, duplication, and unused code)")

    metrics = collector.collect()
    score, grade = collector.calculate_score(metrics)

    if json_output:
        import json
        output = {
            "score": score,
            "grade": grade,
            "metrics": metrics
        }
        print(json.dumps(output, indent=2))
        return

    # ASCII Report
    print("\n" + "="*50)
    print(f" TECHNICAL DEBT REPORT")
    print("="*50)

    # Grade Badge
    color = "\033[92m" # Green
    if grade in ["B", "C"]: color = "\033[93m" # Yellow
    if grade in ["D", "F"]: color = "\033[91m" # Red
    reset = "\033[0m"

    print(f"\nOverall Grade: {color}{grade}{reset} (Score: {int(score)})")
    print(f"Lower score is better. <50=A, <150=B, <300=C, <500=D")

    print("\n--- Breakdown ---")

    # TODOs
    print(f"\n1. TODOs & FIXMEs: {metrics['todos']['count']}")
    if metrics['todos']['count'] > 0:
        print(f"   (Cost: {metrics['todos']['count']} pts)")

    # Complexity
    comp = metrics['complexity']
    print(f"\n2. Complexity Risks: {comp['high_risk_count']} functions > 10")
    print(f"   Avg Complexity: {comp['average']:.1f}")
    if comp['high_risk_items']:
        print("   Top Offenders:")
        for item in comp['high_risk_items']:
            print(f"    - {item['function']} ({item['file']}): {item['complexity']}")

    # Duplication
    dup = metrics['duplication']
    print(f"\n3. Duplication: {dup['blocks']} blocks ({dup['total_tokens']} tokens)")
    if dup['items']:
        print(f"   (Cost: {int(dup['total_tokens']/10)} pts)")

    # Unused
    unused = metrics['unused']
    print(f"\n4. Unused Code: {unused['count']} definitions")
    if unused['count'] > 0:
        print(f"   (Cost: {unused['count'] * 5} pts)")

    print("\n" + "="*50)
