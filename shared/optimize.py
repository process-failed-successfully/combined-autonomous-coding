import sys
import subprocess
import pstats
import io
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from shared.config import Config
from agents.shared.prompts import get_optimize_prompt
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)

class OptimizationManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    async def optimize_script(
        self,
        script_path: Path,
        script_args: List[str] = None,
        agent_type: str = "gemini",
        model: Optional[str] = None,
        limit: int = 20
    ) -> bool:
        """
        Profiles a Python script and uses AI to suggest optimizations.
        """
        script_path = script_path.resolve()
        if not script_path.exists():
            print(f"❌ Error: Script '{script_path}' not found.", file=sys.stderr)
            return False

        print(f"--- Profiling {script_path.name} ---")

        # 1. Run cProfile
        stats_file = self.project_dir / ".profile.stats"
        cmd = [sys.executable, "-m", "cProfile", "-o", str(stats_file), str(script_path)]
        if script_args:
            cmd.extend(script_args)

        print(f"Running: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, cwd=self.project_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Script failed with exit code {e.returncode}. Profiling data might be incomplete.", file=sys.stderr)
            if not stats_file.exists():
                return False

        if not stats_file.exists():
            print("❌ Error: No profiling data generated.", file=sys.stderr)
            return False

        # 2. Parse Stats
        print("\nAnalyzing profile data...")
        stats_buffer = io.StringIO()
        try:
            p = pstats.Stats(str(stats_file), stream=stats_buffer)
            p.strip_dirs().sort_stats("cumtime").print_stats(limit)
        except Exception as e:
            print(f"❌ Error parsing stats: {e}", file=sys.stderr)
            return False

        stats_text = stats_buffer.getvalue()
        print(stats_text)

        # 3. Read Source Code
        try:
            source_code = script_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"❌ Error reading source code: {e}", file=sys.stderr)
            return False

        # 4. Ask Agent
        print("\n--- Requesting AI Optimization Analysis ---")

        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False,
            max_iterations=1,
            stream_output=True,
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            print(f"❌ Unknown agent type: {agent_type}", file=sys.stderr)
            return False

        agent = agent_class(config)
        prompt_template = get_optimize_prompt()

        prompt = prompt_template.format(
            filename=script_path.name,
            limit=limit,
            stats=stats_text,
            code=source_code
        )

        await agent.run_agent_session(prompt)

        if stats_file.exists():
            stats_file.unlink()

        return True

async def run_optimize_logic(args):
    """Entry point for optimize logic."""
    manager = OptimizationManager(args.project_dir)

    script_path = Path(args.script)
    if not script_path.is_absolute():
        script_path = args.project_dir / script_path

    await manager.optimize_script(
        script_path=script_path,
        script_args=args.args,
        agent_type=args.agent,
        model=args.model,
        limit=args.limit
    )
