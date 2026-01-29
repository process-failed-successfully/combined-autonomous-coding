from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.complexity import analyze_project_complexity, process_file

class KataManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def list_challenges(self, limit: int = 10, threshold: int = 5) -> List[Dict[str, Any]]:
        """Finds high-complexity functions to refactor."""
        all_results = analyze_project_complexity(self.project_dir)
        # Filter for complexity > threshold
        # Sort by complexity (desc) then by filename (asc) for stability
        high_risk = sorted(
            [r for r in all_results if r["complexity"] > threshold],
            key=lambda x: (-x["complexity"], x["file"])
        )
        return high_risk[:limit]

    def verify_improvement(self, file_path: str, function_name: str, original_complexity: int) -> Dict[str, Any]:
        """Verifies if the complexity of a function has improved."""
        full_path = self.project_dir / file_path
        if not full_path.exists():
            return {"success": False, "message": "File not found."}

        # Analyze just this file
        results = process_file(full_path, self.project_dir)
        target = next((r for r in results if r["function"] == function_name), None)

        if not target:
            return {"success": False, "message": f"Function '{function_name}' not found in {file_path}."}

        current_complexity = target["complexity"]

        if current_complexity < original_complexity:
            improvement = original_complexity - current_complexity
            return {
                "success": True,
                "message": f"Great job! Complexity reduced from {original_complexity} to {current_complexity} (-{improvement}).",
                "current_complexity": current_complexity,
                "original_complexity": original_complexity
            }
        elif current_complexity == original_complexity:
             return {
                "success": False,
                "message": f"Complexity is still {current_complexity}. Try simplifying the logic.",
                "current_complexity": current_complexity,
                "original_complexity": original_complexity
            }
        else:
             return {
                "success": False,
                "message": f"Oops! Complexity increased to {current_complexity} (+{current_complexity - original_complexity}).",
                "current_complexity": current_complexity,
                "original_complexity": original_complexity
            }
