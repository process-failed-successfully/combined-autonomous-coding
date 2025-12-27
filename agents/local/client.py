import json
import logging
import os
from typing import Any, Dict, Optional, Callable
from pathlib import Path

from shared.config import Config
from agents.shared.base_client import BaseClient
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LocalClient(BaseClient):
    """Handles interactions with the Local LLM (via Ollama)."""

    def __init__(self, config: Config):
        super().__init__(config)
        # Assuming Ollama is running on localhost:11434 (mapped in docker-compose)
        # or via service name 'ollama' if running in the same network.
        # Since 'agent' service shares 'default' network with 'ollama', we can use 'http://ollama:11434/v1'
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434/v1")
        self.api_key = "ollama"  # key is required but ignored
        self.client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)

    async def run_command(
        self,
        prompt: str,
        cwd: Path,
        status_callback: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send prompt to Local LLM and return the response.
        """
        logger.debug(f"Sending request to Local LLM at {self.base_url}...")

        if self.config.verify_creation:
            logger.info("VERIFICATION MODE: Returning mock response.")
            mock_content = {
                "London": 45.0,
                "New York": 25.0,
                "Paris": 30.0,
                "Tokyo": 100.0,
            }
            mock_json = json.dumps(mock_content, indent=4)
            return {
                "content": f"I will create the output.json file.\n```write:output.json\n{mock_json}\n```"
            }

        model = self.config.model
        if not model:
             # Fallback if config model is None (though PostInit handles it)
             from shared.config import DEFAULT_MODEL_LOCAL
             model = DEFAULT_MODEL_LOCAL

        try:
            # We must ensure the model exists.
            # However, for performance, we might just try to generate.
            # If it fails, we could try to pull.
            # But here we just assume it's there or that the user/setup handled it.
            # We can also add a simple check/pull mechanism if needed, but let's keep it simple first.

            if status_callback:
                status_callback(output_line="Waiting for response from Local LLM...")

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful autonomous coding agent."},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )

            collected_content = []
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    collected_content.append(content)
                    if self.config.stream_output:
                        print(content, end="", flush=True)
                    if status_callback:
                        status_callback(output_line=content)

            full_response = "".join(collected_content)
            if self.config.stream_output:
                print() # Newline after stream

            return {"content": full_response}

        except Exception as e:
            logger.exception(f"Error communicating with Local LLM: {e}")
            # If model not found, we might want to suggest pulling it.
            if "model" in str(e) and "not found" in str(e).lower():
                 logger.error(f"Model '{model}' not found. Please ensure it is pulled in Ollama: `ollama pull {model}`")
            raise
