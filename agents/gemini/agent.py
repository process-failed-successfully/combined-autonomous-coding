# Gemini Agent Session Logic
# ==========================
#
# Core agent interaction functions for running autonomous coding sessions using Gemini CLI.

import json
import logging
import time
from typing import Optional, Any, List, Tuple, Dict

from shared.config import Config
from shared.utils import get_file_tree, process_response_blocks
from shared.telemetry import get_telemetry
from shared.agent_client import AgentClient
from agents.shared.base_agent import BaseAgent
from .client import GeminiClient


logger = logging.getLogger(__name__)


async def run_agent_session(
    client: GeminiClient,
    prompt: str,
    history: Optional[List[str]] = None,
    status_callback: Optional[Any] = None,
) -> Tuple[str, str, List[str]]:
    """
    Run a single agent session using Gemini CLI.
    Standalone function for reusability (e.g. Sprint Mode).
    """
    logger.info("Sending prompt to Gemini...")

    try:
        # INJECT DYNAMIC CONTEXT
        file_tree = get_file_tree(client.config.project_dir)

        # INJECT REALITY CHECK
        feature_status = "Feature List Status: Not found"
        feature_file = client.config.feature_list_path
        if feature_file.exists():
            try:
                features = json.loads(feature_file.read_text())
                total = len(features)
                passing = sum(1 for f in features if f.get("passes", False))
                if total > 0:
                    pct = (passing / total) * 100.0
                else:
                    pct = 0.0

                # Report Feature Metrics
                get_telemetry().record_gauge("feature_completion_count", passing)
                get_telemetry().record_gauge("feature_completion_pct", pct)

                if passing == total:
                    feature_status = f"Feature List Status: ALL {total}/{total} FEATURES PASSING. Project is verified complete."
                else:
                    feature_status = f"Feature List Status: {passing}/{total} passing. You are NOT done until {total}/{total} pass."
            except Exception as e:
                feature_status = f"Feature List Status: Error reading file ({e})"

        history_text = (
            "\n".join([f"- {h}" for h in history]) if history else "None"
        )
        context_block = f"""
CURRENT CONTEXT:
Working Directory: {client.config.project_dir}
{feature_status}
RECENT ACTIONS:
{history_text}

{file_tree}
"""
        # Append Jira Prompt Injection if applicable
        jira_context = ""
        if client.config.jira and client.config.agent_id and "JIRA" in client.config.agent_id:
            jira_context = "\n\nCRITICAL: You are working on a JIRA TICKET. You MUST provide frequent updates to the ticket by using the `jira_comment` tool or simply stating your progress clearly so I can post it."

        augmented_prompt = (
            prompt
            + f"\n{context_block}{jira_context}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search."
        )

        # Truncation Logic
        MAX_PROMPT_CHARS = 100000
        if len(augmented_prompt) > MAX_PROMPT_CHARS:
            logger.warning(f"Prompt length ({len(augmented_prompt)}) exceeds limit. Truncating.")
            truncated_file_tree = file_tree[:5000] + "\n... (File tree truncated)"
            context_block = f"""
CURRENT CONTEXT:
Working Directory: {client.config.project_dir}
{feature_status}
RECENT ACTIONS:
{history_text}

{truncated_file_tree}
"""
            augmented_prompt = prompt + f"\n{context_block}{jira_context}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search."

        logger.debug(f"Sending Augmented Prompt:\n{augmented_prompt}")

        # Measure LLM Latency
        start_time = time.time()

        # Define callback to update dashboard status
        current_turn_log = []

        def local_status_update(current_task=None, output_line=None):
            if status_callback:
                status_callback(current_task=current_task, output_line=output_line)

            if not client.agent_client:
                return

            updates: Dict[str, Any] = {}
            if current_task:
                updates["current_task"] = current_task

            if output_line:
                clean_line = output_line.rstrip()
                if clean_line:
                    current_turn_log.append(clean_line)
                    updates["last_log"] = current_turn_log[-30:]

            client.agent_client.report_state(**updates)

        result = await client.run_command(
            augmented_prompt,
            client.config.project_dir,
            status_callback=local_status_update,
        )
        latency = time.time() - start_time
        get_telemetry().record_histogram(
            "llm_latency_seconds",
            latency,
            labels={"model": client.config.model or "unknown", "operation": "generate_content"},
        )

        response_text = ""
        # Handle result structure from Gemini API
        if "candidates" in result:
            for candidate in result["candidates"]:
                for part in candidate.get("content", {}).get("parts", []):
                    if "text" in part:
                        response_text += part["text"]
        elif "content" in result:
            response_text = result.get("content", "")
        elif "response" in result:
            response_text = result.get("response", "")
        else:
            if result:
                logger.debug(f"Full result keys: {result.keys()}")

        if response_text:
            logger.info("Received response from Gemini.")
            logger.debug(f"Response:\n{response_text}")
        else:
            logger.warning("No text content found in Gemini response.")
            logger.info(f"Full Gemini response: {json.dumps(result, indent=2)}")

        # Record Token Usage if available
        if "usageMetadata" in result:
            usage = result["usageMetadata"]
            prompt_tokens = usage.get("promptTokenCount", 0)
            candidates_tokens = usage.get("candidatesTokenCount", 0)

            get_telemetry().increment_counter(
                "llm_tokens_total",
                prompt_tokens,
                labels={"model": client.config.model or "unknown", "type": "input"},
            )
            get_telemetry().increment_counter(
                "llm_tokens_total",
                candidates_tokens,
                labels={"model": client.config.model or "unknown", "type": "output"},
            )

        # Execute any blocks found in the response
        executed_actions = []
        if response_text:
            logger.info("Processing response blocks...")

            def block_status_update(msg):
                local_status_update(current_task=msg)

            log, actions = await process_response_blocks(
                response_text,
                client.config.project_dir,
                client.config.bash_timeout,
                status_callback=block_status_update,
            )
            executed_actions.extend(actions)
            logger.debug(f"Executed actions: {executed_actions}")

            # If the LLM returned a response but no actions, it might be done
            if not executed_actions and response_text:
                logger.info("LLM returned a response but no actions. Assuming completion.")
                return "done", response_text, executed_actions

        return "continue", response_text, executed_actions

    except Exception as e:
        logger.error(f"Error during agent session: {e}", exc_info=True)
        return "error", str(e), []


class GeminiAgent(BaseAgent):
    """
    Gemini-specific implementation of the autonomous agent.
    """

    def get_agent_type(self) -> str:
        return "gemini"

    async def run_agent_session(
        self,
        prompt: str,
        status_callback: Optional[Any] = None,
    ) -> Tuple[str, str, List[str]]:
        """
        Run a single agent session using Gemini CLI.
        """
        client = GeminiClient(self.config)
        # Pass the agent client for status reporting
        setattr(client, "agent_client", self.agent_client)

        return await run_agent_session(client, prompt, self.recent_history, status_callback)


async def run_autonomous_agent(config: Config, agent_client: Optional[AgentClient] = None):
    """
    Compatibility wrapper for running the Gemini autonomous agent.
    """
    agent = GeminiAgent(config, agent_client)
    await agent.run_autonomous_loop()
