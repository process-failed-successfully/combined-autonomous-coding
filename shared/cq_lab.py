import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from shared.complexity import analyze_project_complexity
from shared.duplication import find_duplicates
from shared.security import SecurityAuditor
from shared.debt import DebtCollector
from shared.stats_lab import CodeStatsManager

class CodeQualityManager:
    """
    Aggregates code quality metrics and provides a unified score.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.history_file = self.project_dir / ".cq_history.json"

    def collect_metrics(self) -> Dict[str, Any]:
        """Collects all quality metrics."""
        metrics = {}

        # 1. Complexity
        complexity_data = analyze_project_complexity(self.project_dir)
        metrics["complexity"] = {
            "average": sum(c["complexity"] for c in complexity_data) / len(complexity_data) if complexity_data else 0,
            "max": max((c["complexity"] for c in complexity_data), default=0),
            "high_risk_count": len([c for c in complexity_data if c["complexity"] > 10]),
            "details": sorted(complexity_data, key=lambda x: x["complexity"], reverse=True)[:20] # Top 20
        }

        # 2. Duplication
        duplicates = find_duplicates(self.project_dir, min_tokens=50)
        metrics["duplication"] = {
            "blocks": len(duplicates),
            "total_tokens": sum(d["token_count"] for d in duplicates),
            "details": duplicates[:20] # Top 20
        }

        # 3. Security
        auditor = SecurityAuditor(self.project_dir)
        findings = auditor.run_all(scan_type="all", severity="low")
        metrics["security"] = {
            "count": len(findings),
            "high": len([f for f in findings if f.get("severity") == "HIGH"]),
            "medium": len([f for f in findings if f.get("severity") == "MEDIUM"]),
            "low": len([f for f in findings if f.get("severity") == "LOW"]),
            "details": findings
        }

        # 4. Tech Debt (TODOs/Unused)
        debt_collector = DebtCollector(self.project_dir)
        debt_raw = debt_collector.collect()
        metrics["debt"] = {
            "todos": debt_raw["todos"]["count"],
            "unused": debt_raw["unused"]["count"],
            "details_todos": debt_raw["todos"]["items"][:20],
            "details_unused": debt_raw["unused"]["items"][:20]
        }

        # 5. Stats (LOC)
        stats_mgr = CodeStatsManager(self.project_dir)
        stats_data = stats_mgr.scan()

        # Aggregate totals
        total_files = sum(lang["files"] for lang in stats_data.values())
        total_lines = sum(lang["lines"] for lang in stats_data.values())
        total_code = sum(lang["code"] for lang in stats_data.values())

        metrics["stats"] = {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_code": total_code
        }

        return metrics

    def calculate_score(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates a weighted score (0-100) and grade."""

        # Penalties
        penalty_complexity = (metrics["complexity"]["high_risk_count"] * 2) + (max(0, metrics["complexity"]["average"] - 5) * 2)
        penalty_duplication = (metrics["duplication"]["blocks"] * 1) + (metrics["duplication"]["total_tokens"] / 100)
        penalty_security = (metrics["security"]["high"] * 20) + (metrics["security"]["medium"] * 5) + (metrics["security"]["low"] * 1)
        penalty_debt = (metrics["debt"]["todos"] * 0.5) + (metrics["debt"]["unused"] * 2)

        total_penalty = penalty_complexity + penalty_duplication + penalty_security + penalty_debt

        # Normalize to 0-100
        # A baseline "perfect" score is 100. We subtract penalties.
        # We clamp at 0.
        raw_score = 100 - total_penalty
        score = max(0, min(100, raw_score))

        # Grade
        if score >= 90: grade = "A"
        elif score >= 80: grade = "B"
        elif score >= 70: grade = "C"
        elif score >= 60: grade = "D"
        else: grade = "F"

        return {
            "score": score,
            "grade": grade,
            "penalties": {
                "complexity": penalty_complexity,
                "duplication": penalty_duplication,
                "security": penalty_security,
                "debt": penalty_debt
            }
        }

    def save_history(self, score_data: Dict[str, Any]) -> None:
        """Saves the current score to history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "score": score_data["score"],
            "grade": score_data["grade"],
            "penalties": score_data["penalties"]
        }

        history = []
        if self.history_file.exists():
            try:
                history = json.loads(self.history_file.read_text())
            except Exception:
                pass

        history.append(entry)
        # Keep last 100
        history = history[-100:]

        self.history_file.write_text(json.dumps(history, indent=2))

    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieves history."""
        if not self.history_file.exists():
            return []
        try:
            return json.loads(self.history_file.read_text())
        except Exception:
            return []

def run_cq_lab_logic(args):
    """CLI Entry point for CQ Lab."""
    project_dir = args.project_dir.resolve()

    if args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching Code Quality Lab TUI...")
        app = AgentTUI(project_dir=project_dir, start_tab="tab-cq-lab")
        app.run()
        sys.exit(0)

    manager = CodeQualityManager(project_dir)
    print(f"--- Analyzing Code Quality: {project_dir.name} ---")

    metrics = manager.collect_metrics()
    result = manager.calculate_score(metrics)

    manager.save_history(result)

    if args.json:
        output = {
            "score": result,
            "metrics": metrics
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    # ASCII Report
    grade_color = "\033[92m" if result["grade"] == "A" else "\033[93m" if result["grade"] in ["B", "C"] else "\033[91m"
    reset = "\033[0m"

    print(f"\nOverall Grade: {grade_color}{result['grade']}{reset} ({result['score']:.1f}/100)")
    print("-" * 40)
    print(f"Complexity:  {metrics['complexity']['high_risk_count']} high risk functions (Avg: {metrics['complexity']['average']:.1f})")
    print(f"Duplication: {metrics['duplication']['blocks']} blocks ({metrics['duplication']['total_tokens']} tokens)")
    print(f"Security:    {metrics['security']['high']} High, {metrics['security']['medium']} Medium, {metrics['security']['low']} Low")
    print(f"Tech Debt:   {metrics['debt']['todos']} TODOs, {metrics['debt']['unused']} Unused Items")
    print("-" * 40)
