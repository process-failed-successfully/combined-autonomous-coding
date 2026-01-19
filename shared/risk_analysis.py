"""
Risk Analysis Module
====================

Combines code complexity and git churn metrics to identify high-risk files (Hotspots).
Risk = Complexity * Churn
"""

from pathlib import Path
from .complexity import analyze_project_complexity
from .analytics import get_git_hotspots

class RiskAnalyzer:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def analyze(self, limit: int = 20):
        """
        Analyzes the project for risk.
        Returns a sorted list of dictionaries with risk metrics.
        """
        # 1. Complexity
        complexity_data = analyze_project_complexity(self.project_dir)
        # Aggregate by file
        file_complexity = {}
        for item in complexity_data:
            f = item['file']
            file_complexity[f] = file_complexity.get(f, 0) + item['complexity']

        # 2. Churn (Hotspots)
        # We need all files, so we pass limit=None
        hotspots = get_git_hotspots(self.project_dir, limit=None)
        file_churn = dict(hotspots)

        # 3. Combine
        results = []
        all_files = set(file_complexity.keys()) | set(file_churn.keys())

        for f in all_files:
            c = file_complexity.get(f, 0)
            ch = file_churn.get(f, 0)

            # Risk Score Formula
            # Risk = Complexity * Churn
            # We treat churn=0 as 1 for the calculation if complexity exists,
            # to surface complex files that just haven't changed *yet* (potential landmines).
            # But typically Hotspot analysis requires *activity*.
            # Let's stick to the classic: Risk = Complexity * Churn.
            # If Churn is 0, Risk is 0 (Stable Code).
            # If Complexity is 0, Risk is 0 (Simple Code).

            # However, in a new repo or shallow clone, churn might be 1 for everything.

            score = c * ch

            if score > 0:
                results.append({
                    "file": f,
                    "complexity": c,
                    "churn": ch,
                    "score": score
                })

        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

def _run_risk_logic(project_dir: Path, limit: int = 20, output_format: str = "table"):
    """
    Runs the risk analysis and prints the results.
    """
    analyzer = RiskAnalyzer(project_dir)
    results = analyzer.analyze(limit)

    if not results:
        print("No risk data found (check if this is a git repo and has python files).")
        return

    print(f"--- Risk Analysis (Hotspots) for {project_dir.resolve().name} ---")
    print("Risk = Complexity * Churn")
    print("-" * 75)

    # ANSI Colors
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    print(f"{BOLD}{'Risk Score':<12} | {'Complexity':<10} | {'Churn':<8} | {'File'}{RESET}")
    print("-" * 75)

    for r in results:
        score = r['score']

        # Color coding for score
        color = ""
        if score > 100:
            color = RED
        elif score > 50:
            color = YELLOW

        print(f"{color}{score:<12} | {r['complexity']:<10} | {r['churn']:<8} | {r['file']}{RESET}")

    print("-" * 75)
