import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from shared.dependencies import DependencyAnalyzer
from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

class ResumeGenerator:
    """
    Generates a 'Project Resume' (One-Pager) summarizing the project's state,
    stats, tech stack, and features.
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.analyzer = DependencyAnalyzer(self.project_dir)

    def collect_git_stats(self) -> Dict[str, Any]:
        """Collects basic statistics from the git repository."""
        git_path = shutil.which("git")
        if not git_path or not (self.project_dir / ".git").is_dir():
            return {"status": "Not a git repository"}

        stats = {}
        try:
            # Commit count
            res = subprocess.run(
                [git_path, "-C", str(self.project_dir), "rev-list", "--count", "HEAD"],
                capture_output=True, text=True
            )
            if res.returncode == 0:
                stats["commit_count"] = int(res.stdout.strip())

            # Contributors
            res = subprocess.run(
                [git_path, "-C", str(self.project_dir), "shortlog", "-s", "-n", "HEAD"],
                capture_output=True, text=True
            )
            if res.returncode == 0:
                contributors = []
                for line in res.stdout.strip().split('\n'):
                    if line:
                        parts = line.strip().split('\t')
                        if len(parts) == 2:
                            contributors.append({"count": int(parts[0]), "name": parts[1]})
                stats["contributors"] = contributors

            # First commit date (Project Start)
            res = subprocess.run(
                [git_path, "-C", str(self.project_dir), "log", "--reverse", "--format=%ad", "--date=short", "-n", "1"],
                capture_output=True, text=True
            )
            if res.returncode == 0:
                stats["start_date"] = res.stdout.strip()

            # Last commit date (Last Update)
            res = subprocess.run(
                [git_path, "-C", str(self.project_dir), "log", "-1", "--format=%ad", "--date=short"],
                capture_output=True, text=True
            )
            if res.returncode == 0:
                stats["last_update"] = res.stdout.strip()

        except Exception as e:
            logger.error(f"Error collecting git stats: {e}")
            stats["error"] = str(e)

        return stats

    def detect_tech_stack(self) -> Dict[str, List[str]]:
        """Detects the tech stack using DependencyAnalyzer."""
        scan_results = self.analyzer.scan()
        stack = {"languages": [], "libraries": []}

        if scan_results.get("python"):
            stack["languages"].append("Python")
            for file_info in scan_results["python"]:
                for dep in file_info.get("dependencies", []):
                    stack["libraries"].append(dep["name"])

        if scan_results.get("node"):
            # Could be JS or TS
            has_ts = any(f.suffix == ".ts" for f in self.project_dir.rglob("*.ts"))
            stack["languages"].append("TypeScript" if has_ts else "JavaScript")
            for file_info in scan_results["node"]:
                for dep in file_info.get("dependencies", []):
                    stack["libraries"].append(dep["name"])

        # Go check (DependencyAnalyzer might not cover Go deeply yet, but setup does)
        if (self.project_dir / "go.mod").exists():
            stack["languages"].append("Go")

        # Deduplicate
        stack["languages"] = sorted(list(set(stack["languages"])))
        stack["libraries"] = sorted(list(set(stack["libraries"])))
        return stack

    def get_features(self) -> List[str]:
        """Reads features from feature_list.json."""
        feature_file = self.project_dir / "feature_list.json"
        if not feature_file.exists():
            return []
        try:
            features = json.loads(feature_file.read_text())
            if isinstance(features, list):
                # Filter done features if possible, or just list top ones
                # Assuming simple list of strings for now based on other code
                return features[:10] # Top 10
        except Exception:
            pass
        return []

    async def generate_executive_summary(self, agent_type: str = "gemini", model: Optional[str] = None) -> str:
        """Uses an AI agent to generate an executive summary."""

        # Gather context
        readme_path = self.project_dir / "README.md"
        readme_content = readme_path.read_text() if readme_path.exists() else "No README found."

        spec_path = self.project_dir / "app_spec.txt"
        spec_content = spec_path.read_text() if spec_path.exists() else "No spec found."

        stats = self.collect_git_stats()
        stack = self.detect_tech_stack()

        context = f"""
        Project Name: {self.project_dir.name}
        Tech Stack: {', '.join(stack['languages'])}
        Key Libraries: {', '.join(stack['libraries'][:10])}
        Commits: {stats.get('commit_count', 'Unknown')}
        Started: {stats.get('start_date', 'Unknown')}

        -- README --
        {readme_content[:2000]}

        -- APP SPEC --
        {spec_content[:2000]}
        """

        prompt = f"""
        You are a CTO writing a "Project Resume" (One-Pager) for this repository.

        Based on the context below, write a professional "Executive Summary" (150-200 words).
        Focus on:
        1. What the project does (Core Value Proposition).
        2. The technical architecture/approach (briefly).
        3. The current maturity/status.

        Tone: Professional, Concise, Impressive.
        Do not use markdown headers (##), just the text paragraphs.

        Context:
        {context}
        """

        # Init Agent
        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            max_iterations=1,
            stream_output=False
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
            status, response, _ = await agent.run_agent_session(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Could not generate executive summary due to an error."

    async def render(self, agent_type: str = "gemini", model: Optional[str] = None) -> str:
        """Renders the full Project Resume in Markdown."""

        print("Gathering data...")
        stats = self.collect_git_stats()
        stack = self.detect_tech_stack()
        features = self.get_features()

        print(f"Generating Executive Summary with {agent_type}...")
        summary = await self.generate_executive_summary(agent_type, model)

        # Template
        project_name = self.project_dir.name.replace("-", " ").title()
        date_str = datetime.now().strftime("%Y-%m-%d")

        md = f"# Project Resume: {project_name}\n\n"
        md += f"**Generated:** {date_str}\n\n"

        md += "## 📋 Executive Summary\n\n"
        md += f"{summary}\n\n"

        md += "## 🛠 Tech Stack\n\n"
        md += f"- **Languages:** {', '.join(stack['languages']) or 'None detected'}\n"
        md += f"- **Key Libraries:** {', '.join(stack['libraries']) or 'None detected'}\n\n"

        md += "## 📊 Vital Statistics\n\n"
        md += "| Metric | Value |\n"
        md += "|---|---|\n"
        md += f"| **Total Commits** | {stats.get('commit_count', 'N/A')} |\n"
        md += f"| **Contributors** | {len(stats.get('contributors', []))} |\n"
        md += f"| **First Commit** | {stats.get('start_date', 'N/A')} |\n"
        md += f"| **Last Update** | {stats.get('last_update', 'N/A')} |\n"
        md += "\n"

        if stats.get('contributors'):
            md += "### Top Contributors\n"
            for c in stats['contributors'][:5]:
                md += f"- {c['name']} ({c['count']} commits)\n"
            md += "\n"

        md += "## 🚀 Key Features\n\n"
        if features:
            for feat in features:
                md += f"- {feat}\n"
        else:
            md += "No explicit features listed in `feature_list.json`.\n"

        return md

async def run_resume_logic(project_dir: Path, output: Path = None, agent_type: str = "gemini", model: str = None):
    generator = ResumeGenerator(project_dir)
    content = await generator.render(agent_type, model)

    if output:
        output.write_text(content, encoding="utf-8")
        print(f"\n✅ Project Resume saved to: {output}")
    else:
        print("\n" + content)
