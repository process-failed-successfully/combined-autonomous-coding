import json
import logging
import os
from typing import Any, Dict, Optional, Callable
from pathlib import Path

from shared.config import Config
from agents.shared.base_client import BaseClient
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class OpenRouterClient(BaseClient):
    """Handles interactions with OpenRouter API."""

    def __init__(self, config: Config):
        super().__init__(config)
        self.base_url = "https://openrouter.ai/api/v1"
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        if self.config.verify_creation and not self.api_key:
            self.api_key = "sk-or-v1-mock-key"
        
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY not found in environment.")
        
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/google-deepmind/combined-autonomous-coding",
                "X-Title": "Combined Autonomous Coding"
            }
        )

    async def run_command(
        self,
        prompt: str,
        cwd: Path,
        status_callback: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send prompt to OpenRouter and return the response.
        """
        logger.debug(f"Sending request to OpenRouter...")

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
             from shared.config import DEFAULT_MODEL_OPENROUTER
             model = DEFAULT_MODEL_OPENROUTER

        try:
            if status_callback:
                status_callback(output_line="Waiting for response from OpenRouter...")

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful autonomous coding agent."},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )

            collected_content = []
            usage = None
            async for chunk in response:
                if not chunk.choices:
                    # Some providers send usage in a chunk with no choices or empty choices
                    if not usage and hasattr(chunk, "usage") and chunk.usage:
                         usage = chunk.usage
                    continue
                
                delta = chunk.choices[0].delta
                content = delta.content
                if content:
                    collected_content.append(content)
                    if self.config.stream_output:
                        print(content, end="", flush=True)
                    if status_callback:
                        status_callback(output_line=content)
                
                # Check for usage in chunk (often last chunk)
                if not usage and hasattr(chunk, "usage") and chunk.usage:
                    usage = chunk.usage

            full_response = "".join(collected_content)
            if self.config.stream_output:
                print() # Newline after stream
            
            result = {"content": full_response}
            if usage:
                result["usage"] = {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                }
            
            return result

        except Exception as e:
            logger.exception(f"Error communicating with OpenRouter: {e}")
            raise
