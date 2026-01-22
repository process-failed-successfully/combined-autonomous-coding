"""
Optimization Manager
====================

Manages the execution of performance profiling and AI-driven optimization suggestions.
"""

import sys
import pstats
import subprocess
import logging
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

from shared.config import Config
from agents.shared.prompts import get_optimize_prompt

logger = logging.getLogger(__name__)

class OptimizationManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def run_profile(self, script_path: Path, args: List[str]) -> Optional[Path]:
        """Runs the script with cProfile and returns the stats file path."""
        stats_file = self.project_dir / ".agent_profile.stats"
        # We run the script as a module if possible? No, script path is safest.
        cmd = [sys.executable, "-m", "cProfile", "-o", str(stats_file), str(script_path)] + args

        print(f"Running profiler: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, cwd=self.project_dir, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Profiling failed:\n{result.stderr}")
                # Sometimes the script fails but profile is generated?
                # But if it fails, the profile might be incomplete or misleading.
                if not stats_file.exists():
                     return None
                print("⚠️  Script failed but stats file exists. Proceeding with caution.")
            return stats_file
        except Exception as e:
            print(f"❌ Error running profiler: {e}")
            return None

    def analyze_stats(self, stats_file: Path, limit: int = 10) -> List[Dict[str, Any]]:
        """Parses the stats file and returns the top functions."""
        try:
            p = pstats.Stats(str(stats_file))
            # Sort by total time spent in the function (excluding calls)
            # This highlights expensive functions.
            # 'cumtime' is also useful. Let's provide both metrics in the output but sort by tottime.
            p.sort_stats("tottime")

            all_funcs = []
            for func, (cc, nc, tt, ct, callers) in p.stats.items():  # type: ignore
                filename, line, name = func
                all_funcs.append({
                    "filename": filename,
                    "line": line,
                    "name": name,
                    "ncalls": nc,
                    "tottime": tt,
                    "cumtime": ct
                })

            all_funcs.sort(key=lambda x: x["tottime"], reverse=True)
            return all_funcs[:limit]
        except Exception as e:
            logger.error(f"Error analyzing stats: {e}")
            return []

    def get_source_code(self, filename: str, lineno: int) -> Optional[str]:
        """Extracts source code for a function."""
        # Check if file belongs to project
        file_path = Path(filename)

        # Case 1: Absolute path matches project dir
        if file_path.is_absolute():
            try:
                if not str(file_path).startswith(str(self.project_dir)):
                     # External library file
                     return None
            except ValueError:
                return None
        else:
            # Case 2: Relative path
            file_path = self.project_dir / filename
            if not file_path.exists():
                # Case 3: Maybe just a filename in root
                file_path = self.project_dir / Path(filename).name
                if not file_path.exists():
                    return None

        if not file_path.exists():
             return None

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()

            # Use AST to find the function at the given line
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Node lineno is usually the 'def' line.
                    if node.lineno == lineno:
                        return ast.get_source_segment(source, node)

            # Fallback: AST match failed (maybe lineno is inside body?), grab context
            lines = source.splitlines()
            start = max(0, lineno - 1)
            # Find indentation to guess end?
            # Simple chunk for now
            end = min(len(lines), lineno + 25)
            chunk = "\n".join(lines[start:end])
            return f"# (Approximate source around line {lineno})\n{chunk}"

        except Exception as e:
            logger.warning(f"Error reading source for {filename}: {e}")
            return None

    async def get_ai_suggestions(self, stats_file: Path, agent_type: str = "gemini", model: Optional[str] = None) -> str:
        """Analyzes profiling stats using AI and returns the suggestion text."""
        print("\nAnalyzing profiling data...")
        top_funcs = self.analyze_stats(stats_file)

        if not top_funcs:
            return "No significant functions found to optimize."

        # Prepare Prompt Data
        stats_summary = "Top Functions (by tottime):\n"
        source_context = ""
        user_code_found = False

        for func in top_funcs:
            stats_summary += f"- {func['name']} ({func['filename']}:{func['line']}): tottime={func['tottime']:.4f}s, cumtime={func['cumtime']:.4f}s, ncalls={func['ncalls']}\n"

            if func['line'] > 0:
                code = self.get_source_code(func['filename'], func['line'])
                if code:
                    user_code_found = True
                    source_context += f"\n### Function: {func['name']} in {func['filename']}\n```python\n{code}\n```\n"

        if not user_code_found:
            print("⚠️  Top time-consuming functions seem to be external (libraries/built-ins).")
            print("   The agent will try to advise based on usage patterns.")

        prompt = get_optimize_prompt()
        full_prompt = f"{prompt}\n\n## Profiling Statistics\n{stats_summary}\n\n## Source Code\n{source_context}"

        # Call Agent
        print("🤖 Asking agent for optimizations...")

        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            max_iterations=1,
            stream_output=True
        )

        # Instantiate agent dynamically
        from agents.gemini import GeminiAgent
        from agents.cursor import CursorAgent
        from agents.local import LocalAgent
        from agents.openrouter import OpenRouterAgent
        from shared.base_agent import BaseAgent
        from typing import Type

        agent_map: Dict[str, Type[BaseAgent]] = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent
        }

        agent_class = agent_map.get(agent_type)
        if not agent_class:
            return f"❌ Unknown agent type: {agent_type}"

        agent = agent_class(config)

        try:
            status, response, actions = await agent.run_agent_session(full_prompt)
            return response
        except Exception as e:
            return f"❌ Error querying agent: {e}"

    async def optimize(self, script_path: Path, args: List[str], agent_type: str = "gemini", model: Optional[str] = None):
        """Main entry point."""
        script_full_path = self.project_dir / script_path
        if not script_full_path.exists():
            print(f"❌ Script not found: {script_full_path}")
            return False

        print(f"--- Optimizing {script_path.name} ---")
        stats_file = self.run_profile(script_full_path, args)
        if not stats_file:
            return False

        response = await self.get_ai_suggestions(stats_file, agent_type, model)
        print("\n" + response)
        return True
