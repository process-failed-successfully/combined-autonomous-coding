"""
Cursor Agent Session Logic
==========================

Core agent interaction functions for running autonomous coding sessions using Cursor CLI.
"""

import json
import logging
import time
from typing import Optional, Any, List, Tuple, Dict

from shared.config import Config
from shared.utils import get_file_tree, process_response_blocks
from shared.agent_client import AgentClient
from shared.telemetry import get_telemetry
from agents.shared.base_agent import BaseAgent
from .client import CursorClient


logger = logging.getLogger(__name__)


async def run_agent_session(
    client: CursorClient,
    prompt: str,
    history: Optional[List[str]] = None,
    status_callback: Optional[Any] = None,
) -> Tuple[str, str, List[str]]:
    """
    Run a single agent session using Cursor CLI.
    Standalone function for reusability.
    """
    logger.info("Sending prompt to Cursor Agent...")

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
        if client.config.jira and getattr(client.config, "jira_ticket_key", None):
            jira_context = "\n\nCRITICAL: You are working on a JIRA TICKET. You MUST provide frequent updates to the ticket by using the `jira_comment` tool (if available) or simply stating your progress clearly so I can post it."

        augmented_prompt = (
            prompt +
            f"\n{context_block}{jira_context}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search.")

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
            augmented_prompt = prompt + \
                f"\n{context_block}\n\nREMINDER: Use ```bash for commands, ```write:filename for files, ```read:filename to read, ```search:query to search."

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

        if client.agent_client:
            client.agent_client.report_state(current_task="Sending Prompt to Agent")

        logger.debug(f"Sending Augmented Prompt:\n{augmented_prompt}")

        # Measure LLM Latency
        start_time = time.time()
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
        # Handle result structure from Cursor API
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
            logger.info("Received response from Cursor Agent.")
            if client.agent_client:
                client.agent_client.report_state(current_task="Processing Response")
            logger.debug(f"Response:\n{response_text}")
        else:
            logger.warning("No text content found in Cursor response.")
            logger.info(f"Full Cursor response: {json.dumps(result, indent=2)}")

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
            executed_actions = actions

        return "continue", response_text, executed_actions

    except Exception as e:
        logger.exception("Error during agent session")
        if client.agent_client:
            client.agent_client.report_state(current_task=f"Error: {e}")
        return "error", str(e), []


class CursorAgent(BaseAgent):
    """
    Cursor-specific implementation of the autonomous agent.
    """

    def get_agent_type(self) -> str:
        return "cursor"

    async def run_agent_session(
        self,
        prompt: str,
        status_callback: Optional[Any] = None,
    ) -> Tuple[str, str, List[str]]:
        """
        Run a single agent session using Cursor CLI.
        """
        client = CursorClient(self.config)
        # Inject agent_client if available for reporting
        if self.agent_client:
            setattr(client, "agent_client", self.agent_client)

        return await run_agent_session(client, prompt, self.recent_history, status_callback)


async def run_autonomous_agent(
    config: Config,
    agent_client: Optional[AgentClient] = None,
) -> None:
    """
    Run the autonomous agent loop.
    """
    # Login Mode
    if config.login_mode:
        logger.info("Starting Cursor Login Flow...")
        import subprocess
        try:
            subprocess.run(["cursor-agent", "login"], check=False)
        except FileNotFoundError:
            logger.error("Cursor Agent CLI not found.")
        except Exception as e:
            logger.error(f"Error during login: {e}")
        return

    agent = CursorAgent(config, agent_client)
    await agent.run_autonomous_loop()
