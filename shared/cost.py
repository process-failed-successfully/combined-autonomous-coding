from pathlib import Path
from shared.config_loader import load_config_from_file


class CostCalculator:
    """Calculates the cost of agent runs based on token usage."""

    # Default Pricing (per 1M tokens)
    # These can be overridden by config if needed in the future
    PRICING = {
        "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
        "gemini-1.5-flash": {"input": 0.35, "output": 1.05},
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00}
    }

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config = load_config_from_file()

    def get_pricing(self, model: str) -> dict:
        """Returns pricing for a given model."""
        # Simple fuzzy matching or fallback
        for key, price in self.PRICING.items():
            if key in model.lower():
                return price
        # Default fallback (e.g. flash)
        return self.PRICING["gemini-1.5-flash"]

    def calculate_run_cost(self, run_id: str = None) -> dict:
        """Calculates cost for a specific run ID."""
        if not run_id:
            return {"error": "No run ID provided."}

        # Look for metrics file
        # We assume main.py logs metrics to a file or we parse the run log.
        # Currently, the agent logs "Metrics:" to the run log.
        # We need to find the log file for this run.

        log_dir = self.project_dir / "logs"
        if not log_dir.exists():
            return {"error": "No logs directory found."}

        # Try to find file starting with run_id
        # run_id might be "run_TIMESTAMP_ID" or just "ID"
        # The logs are typically "run_TIMESTAMP_ID.log"
        target_file = None
        for f in log_dir.iterdir():
            if run_id in f.name and f.suffix == ".log":
                target_file = f
                break

        if not target_file:
            # Maybe it's in the .agent_history but file is cleaned?
            return {"error": f"Log file for {run_id} not found."}

        # Parse metrics from log
        metrics = {}
        try:
            with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                # We look for the JSON block logged at the end usually
                # Or specific lines like "Input Tokens: X"
                # The memory says "LogParser" extracts commands.
                # Let's simple regex for now as seen in legacy main.py
                import re

                # Try to find model
                model_match = re.search(r"Model:\s+([^\s]+)", content)
                metrics["model"] = model_match.group(1) if model_match else "unknown"

                # Try to find tokens
                # Usually logged as "Total Tokens: X (Input: Y, Output: Z)" or similar
                # Or "Token Usage: Input: Y, Output: Z"

                input_match = re.search(r"Input Tokens:\s+(\d+)", content)
                output_match = re.search(r"Output Tokens:\s+(\d+)", content)

                if input_match:
                    metrics["input_tokens"] = int(input_match.group(1))
                if output_match:
                    metrics["output_tokens"] = int(output_match.group(1))

                # Fallback if only total is found (older logs)
                if "input_tokens" not in metrics:
                    total_match = re.search(r"LLM Tokens Used:\s+(\d+)", content)
                    if total_match:
                        total = int(total_match.group(1))
                        # Assume 75/25 split
                        metrics["input_tokens"] = int(total * 0.75)
                        metrics["output_tokens"] = total - metrics["input_tokens"]

        except Exception as e:
            return {"error": f"Error parsing log: {e}"}

        if "input_tokens" not in metrics:
            return {"error": "No token usage found in log."}

        # Calculate Cost
        pricing = self.get_pricing(metrics["model"])
        input_cost = (metrics["input_tokens"] / 1_000_000) * pricing["input"]
        output_cost = (metrics["output_tokens"] / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost

        return {
            "run_id": run_id,
            "model": metrics["model"],
            "input_tokens": metrics["input_tokens"],
            "output_tokens": metrics["output_tokens"],
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }

    def calculate_total_cost(self) -> dict:
        """Calculates total cost of all runs in history."""
        history_file = self.project_dir / ".agent_history"
        if not history_file.exists():
            return {"total_cost": 0.0, "details": []}

        total = 0.0
        details = []

        try:
            with open(history_file, "r") as f:
                run_ids = [line.strip() for line in f if line.strip()]

            for run_id in run_ids:
                res = self.calculate_run_cost(run_id)
                if "error" not in res:
                    total += res["total_cost"]
                details.append(res)
        except Exception:
            pass

        return {"total_cost": total, "details": details}

    def check_budget(self) -> dict:
        """Checks total cost against budget limit."""
        data = self.calculate_total_cost()
        current_cost = data["total_cost"]

        limit = self.config.get("budget_limit")

        result = {
            "current": current_cost,
            "limit": limit,
            "remaining": 0.0,
            "percent": 0.0,
            "status": "No Limit"
        }

        if limit is not None:
            limit = float(limit)
            result["limit"] = limit
            result["remaining"] = max(0, limit - current_cost)
            if limit > 0:
                result["percent"] = (current_cost / limit) * 100

            if current_cost > limit:
                result["status"] = "EXCEEDED"
            elif result["percent"] >= 80:
                result["status"] = "WARNING"
            else:
                result["status"] = "OK"

        return result
