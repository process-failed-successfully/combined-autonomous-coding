"""
Presentation Generator
======================

Generates a Marp-compatible Markdown presentation summarizing the project.
"""

import logging
import shutil
import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

from shared.config import Config
from shared.dockerizer import Dockerizer
from shared.cli_utils import _parse_metrics, _find_metrics_file
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from agents.shared.prompts import get_presentation_prompt

logger = logging.getLogger(__name__)

class PresentationGenerator:
    def __init__(self, project_dir: Path, agent_type: str = "gemini", model: Optional[str] = None):
        self.project_dir = project_dir.resolve()
        self.agent_type = agent_type
        self.model = model
        self.dockerizer = Dockerizer(project_dir)

    def collect_context(self) -> str:
        """Gathers project context for the presentation."""
        context = []

        # 1. Project Info
        context.append(f"Project Name: {self.project_dir.name}")
        project_type = self.dockerizer.detect_project_type()
        context.append(f"Detected Tech Stack: {project_type.capitalize()}")

        # 2. Goal (from app_spec.txt)
        spec_path = self.project_dir / "app_spec.txt"
        if spec_path.exists():
            try:
                spec_content = spec_path.read_text(encoding="utf-8", errors="ignore")
                # Truncate if too long
                if len(spec_content) > 1000:
                    spec_content = spec_content[:1000] + "..."
                context.append(f"\nProject Goal (from app_spec.txt):\n{spec_content}")
            except Exception:
                context.append("\nProject Goal: Could not read app_spec.txt")

        # 3. Features (from feature_list.json)
        feature_path = self.project_dir / "feature_list.json"
        if feature_path.exists():
            try:
                features = json.loads(feature_path.read_text())
                passed = [f for f in features if f.get("passes")]
                pending = [f for f in features if not f.get("passes")]

                context.append("\nFeatures:")
                context.append(f"  Total: {len(features)}")
                context.append(f"  Completed: {len(passed)}")
                context.append(f"  Pending: {len(pending)}")

                if passed:
                    context.append("  Highlights (Completed):")
                    for f in passed[:5]:
                        context.append(f"    - {f.get('description', 'Unknown')}")
            except Exception:
                context.append("\nFeatures: Error parsing feature_list.json")
        else:
            context.append("\nFeatures: No feature list found.")

        # 4. Metrics (from final_metrics.txt via _find_metrics_file logic)
        # We try to find the LATEST run's metrics.
        # Check history first
        history_file = self.project_dir / ".agent_history"
        run_id = None
        if history_file.exists():
            try:
                with open(history_file, "r") as f:
                    run_ids = [line.strip() for line in f if line.strip()]
                if run_ids:
                    run_id = run_ids[-1]
            except Exception:
                pass

        metrics_file = None
        if run_id:
            metrics_file = _find_metrics_file(run_id, self.project_dir)

        if not metrics_file:
            metrics_file = self.project_dir / "final_metrics.txt"

        if metrics_file and metrics_file.exists():
            metrics = _parse_metrics(metrics_file)
            context.append("\nLatest Metrics:")
            if "Total Execution Time (s)" in metrics:
                context.append(f"  Execution Time: {metrics['Total Execution Time (s)']}s")
            if "LLM Tokens Used" in metrics:
                context.append(f"  Tokens Used: {metrics['LLM Tokens Used']}")
            if "Total Errors" in metrics:
                context.append(f"  Errors: {metrics['Total Errors']}")
            if "Run ID" in metrics:
                context.append(f"  Run ID: {metrics['Run ID']}")

        # 5. Git Stats
        git_path = shutil.which("git")
        if git_path and (self.project_dir / ".git").is_dir():
            try:
                # Count commits
                count_res = subprocess.run(
                    [git_path, "-C", str(self.project_dir), "rev-list", "--count", "HEAD"],
                    capture_output=True, text=True
                )
                commit_count = count_res.stdout.strip()
                context.append(f"\nGit History: {commit_count} commits")

                # Recent contributors
                log_res = subprocess.run(
                    [git_path, "-C", str(self.project_dir), "shortlog", "-sn", "HEAD"],
                    capture_output=True, text=True
                )
                context.append("Contributors:\n" + log_res.stdout.strip())
            except Exception:
                context.append("\nGit Stats: Unavailable")

        return "\n".join(context)

    async def generate(self, output_file: Path, theme: str = "default") -> bool:
        """Generates the presentation and saves it to the output file."""
        print(f"Collecting project context for {self.project_dir.name}...")
        context_str = self.collect_context()

        print("Generating presentation with AI...")

        config = Config(
            project_dir=self.project_dir,
            agent_type=self.agent_type,
            model=self.model,
            max_iterations=1,
            stream_output=True,
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        agent_class = agent_class_map.get(self.agent_type)
        if not agent_class:
            logger.error(f"Unknown agent type: {self.agent_type}")
            return False

        agent = agent_class(config)

        # Prompt construction
        base_prompt = get_presentation_prompt()
        full_prompt = base_prompt.replace("{user_input}", context_str)
        # Add theme instruction
        full_prompt += f"\n\nPlease use the '{theme}' theme in the frontmatter."

        try:
            status, response, actions = await agent.run_agent_session(full_prompt)

            # Filter response to ensure clean markdown?
            # The prompt asks for ONLY markdown, but agents can be chatty.
            # We'll just save the raw response for now, maybe stripping ```markdown blocks if present.

            content = response
            # Simple extraction if wrapped in code blocks
            match = re.search(r"```markdown\s*(.*?)\s*```", response, re.DOTALL)
            if match:
                content = match.group(1)
            else:
                match = re.search(r"```\s*(.*?)\s*```", response, re.DOTALL)
                if match:
                    content = match.group(1)

            output_file.write_text(content, encoding="utf-8")
            print(f"✅ Presentation saved to: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error generating presentation: {e}")
            print(f"❌ Error: {e}")
            return False

async def run_presentation(
    project_dir: Path,
    output: str = "presentation.md",
    theme: str = "default",
    agent_type: str = "gemini",
    model: Optional[str] = None
) -> bool:
    """CLI entry point for presentation generation."""
    output_path = Path(output)
    if not output_path.is_absolute():
        output_path = project_dir / output_path

    generator = PresentationGenerator(project_dir, agent_type, model)
    return await generator.generate(output_path, theme)
