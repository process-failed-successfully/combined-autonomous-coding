
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from shared.log_explorer import LogParser, AgentStep
from shared.cost import CostCalculator
from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

class RetrospectiveConductor:
    """
    Conducts a retrospective analysis on agent runs.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.log_parser = LogParser()
        self.cost_calculator = CostCalculator(project_dir)

    def get_run_log_path(self, run_id: str = None) -> Optional[Path]:
        """Resolves the log file path for a run ID."""
        log_dir = Path(__file__).parent.parent / "agents" / "logs"

        if not run_id:
            # Get latest from history
            history_file = self.project_dir / ".agent_history"
            if not history_file.exists():
                return None
            with open(history_file, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
                if not lines:
                    return None
                run_id = lines[-1]

        # Find file
        for f in log_dir.glob("*.log"):
            if run_id in f.name:
                return f

        return None

    def analyze_run(self, run_id: str = None) -> Dict[str, Any]:
        """
        Analyzes a specific run and returns metrics.
        """
        log_path = self.get_run_log_path(run_id)
        if not log_path:
            return {"error": "Log file not found."}

        steps = self.log_parser.parse_run(log_path)
        cost_data = self.cost_calculator.calculate_run_cost(run_id or log_path.stem)

        metrics = {
            "run_id": run_id or log_path.stem,
            "timestamp": datetime.fromtimestamp(log_path.stat().st_mtime).isoformat(),
            "total_steps": len(steps),
            "errors": 0,
            "warnings": 0,
            "actions": 0,
            "thoughts": 0,
            "duration_seconds": 0.0, # Placeholder, implies log parsing has timestamps
            "cost": cost_data.get("total_cost", 0.0),
            "patterns": [],
            "summary": ""
        }

        # Calculate metrics
        error_steps = []
        for step in steps:
            if step.type == "ERROR":
                metrics["errors"] += 1
                error_steps.append(step)
            elif step.type == "WARNING":
                metrics["warnings"] += 1
            elif step.type == "ACTION":
                metrics["actions"] += 1
            elif step.type == "THOUGHT":
                metrics["thoughts"] += 1

        # Calculate Duration (First vs Last step)
        if steps:
            try:
                fmt = "%H:%M:%S"
                start = datetime.strptime(steps[0].timestamp, fmt)
                end = datetime.strptime(steps[-1].timestamp, fmt)
                # Handle day rollover if needed, but simple subtraction for now
                diff = end - start
                metrics["duration_seconds"] = diff.total_seconds()
            except Exception:
                pass

        # Detect Patterns
        metrics["patterns"] = self.detect_patterns(steps)
        metrics["steps"] = steps # Keep for AI analysis

        return metrics

    def detect_patterns(self, steps: List[AgentStep]) -> List[Dict[str, Any]]:
        """Detects patterns like loops or repeated errors."""
        patterns = []

        # 1. Repeated Errors
        error_counts = {}
        for step in steps:
            if step.type == "ERROR":
                desc = step.description
                error_counts[desc] = error_counts.get(desc, 0) + 1

        for desc, count in error_counts.items():
            if count > 1:
                patterns.append({
                    "type": "repeated_error",
                    "description": desc,
                    "count": count
                })

        # 2. Action Loops (simplified: same action description repeated consecutively)
        # Or just frequency analysis of actions
        action_counts = {}
        for step in steps:
            if step.type == "ACTION":
                action_counts[step.description] = action_counts.get(step.description, 0) + 1

        for desc, count in action_counts.items():
            if count > 3:
                patterns.append({
                    "type": "potential_loop",
                    "description": desc,
                    "count": count
                })

        return patterns

    async def generate_report(self, analysis: Dict[str, Any], agent_type: str = "gemini", model: str = None) -> str:
        """
        Generates a qualitative retrospective report using AI.
        """
        if "error" in analysis:
            return f"Error analyzing run: {analysis['error']}"

        # Prepare context for AI
        steps_summary = []
        for s in analysis.get("steps", [])[:100]: # Limit context
            steps_summary.append(f"[{s.timestamp}] {s.type}: {s.description}")

        context = "\n".join(steps_summary)

        patterns_str = "\n".join([f"- {p['type']}: {p['description']} (x{p['count']})" for p in analysis["patterns"]])

        prompt = f"""
You are an Agile Coach conducting a Retrospective on an AI Agent's execution run.

**Run Metrics:**
- ID: {analysis['run_id']}
- Duration: {analysis['duration_seconds']}s
- Cost: ${analysis['cost']:.4f}
- Steps: {analysis['total_steps']} (Errors: {analysis['errors']}, Actions: {analysis['actions']})

**Detected Patterns:**
{patterns_str}

**Execution Log Summary:**
{context}

**Task:**
Generate a Markdown Retrospective Report.
Sections:
1.  **Executive Summary**: Was the run successful? What was the main outcome?
2.  **What Went Well**: Highlight efficient actions or good reasoning.
3.  **What Went Wrong**: Analyze errors, loops, or inefficiencies.
4.  **Action Items**: Specific suggestions to improve prompts, tools, or configuration to avoid these issues next time.

Keep it concise and actionable.
"""

        # Initialize Agent
        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            max_iterations=1,
            stream_output=False,
            verbose=False
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        agent_class = agent_class_map.get(agent_type, GeminiAgent)
        agent = agent_class(config)

        try:
            _, report, _ = await agent.run_agent_session(prompt)
            return report
        except Exception as e:
            return f"Error generating AI report: {e}"

async def run_retro_logic(project_dir: Path, run_id: str = None, output: Path = None, agent_type: str = "gemini", model: str = None) -> bool:
    """CLI Entry point logic."""
    conductor = RetrospectiveConductor(project_dir)
    print(f"--- Conducting Retrospective ---")

    analysis = conductor.analyze_run(run_id)
    if "error" in analysis:
        print(f"❌ {analysis['error']}")
        return False

    print(f"Run ID: {analysis['run_id']}")
    print(f"Metrics: {analysis['total_steps']} steps, {analysis['errors']} errors, ${analysis['cost']:.4f}")

    if analysis['patterns']:
        print("\n⚠️  Patterns Detected:")
        for p in analysis['patterns']:
            print(f"  - {p['type']}: {p['description']} (x{p['count']})")

    print("\nGenerating AI Report... (this may take a moment)")
    report = await conductor.generate_report(analysis, agent_type, model)

    print("\n" + "="*40)
    print(report)
    print("="*40 + "\n")

    if output:
        try:
            output.write_text(report, encoding="utf-8")
            print(f"✅ Report saved to {output}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")

    return True
