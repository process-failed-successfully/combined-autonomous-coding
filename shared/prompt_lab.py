import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from shared.config import Config
# Import agents lazily to avoid circular deps if needed, but standard imports are fine here
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent

logger = logging.getLogger(__name__)


class PromptLabManager:
    """Manages prompt experiments for the Prompt Lab."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.experiments_dir = project_dir / ".agent_experiments"
        self.experiments_dir.mkdir(parents=True, exist_ok=True)

    def list_experiments(self) -> List[str]:
        """Lists saved experiments."""
        if not self.experiments_dir.exists():
            return []
        return sorted([f.stem for f in self.experiments_dir.glob("*.json")])

    def save_experiment(self, name: str, data: Dict[str, Any]) -> None:
        """Saves an experiment configuration."""
        file_path = self.experiments_dir / f"{name}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_experiment(self, name: str) -> Optional[Dict[str, Any]]:
        """Loads an experiment configuration."""
        file_path = self.experiments_dir / f"{name}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def delete_experiment(self, name: str) -> bool:
        """Deletes an experiment."""
        file_path = self.experiments_dir / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def run_experiment(
        self,
        system_prompt: str,
        user_prompt: str,
        agent_types: List[str],
        models: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Runs the prompt against the selected agents.

        Args:
            system_prompt: The system prompt (if supported) or prepended context.
            user_prompt: The user query.
            agent_types: List of agent types to run (e.g. ['gemini', 'local']).
            models: Optional dict mapping agent_type to model name.

        Returns:
            Dict mapping agent_type to the response string.
        """
        results = {}
        tasks = []

        # Combine prompts for agents that might not support distinct system prompts easily via this interface
        # For this lab, we'll construct a full prompt.
        full_prompt = ""
        if system_prompt:
            full_prompt += f"System:\n{system_prompt}\n\n"
        full_prompt += f"User:\n{user_prompt}"

        for agent_type in agent_types:
            model = models.get(agent_type) if models else None
            tasks.append(self._run_single_agent(agent_type, full_prompt, model))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for agent_type, response in zip(agent_types, responses):
            if isinstance(response, Exception):
                results[agent_type] = f"Error: {str(response)}"
            else:
                results[agent_type] = response

        return results

    async def _run_single_agent(self, agent_type: str, prompt: str, model: Optional[str]) -> str:
        """Helper to run a single agent."""
        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            verbose=False,
            max_iterations=1,
            stream_output=False
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }

        agent_class = agent_class_map.get(agent_type)
        if not agent_class:
            return f"Unknown agent type: {agent_type}"

        try:
            # Initialize agent
            agent = agent_class(config)

            # Run session
            # Note: run_agent_session returns (status, response, actions)
            # We are interested in response.
            status, response, actions = await agent.run_agent_session(prompt)

            return response
        except Exception as e:
            logger.error(f"Error running {agent_type}: {e}")
            raise e
