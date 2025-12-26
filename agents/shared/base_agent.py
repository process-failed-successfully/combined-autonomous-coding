"""
Base Agent Abstract Class
=========================

Defines the shared autonomous agent loop and state management
"""

import abc
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Any, Tuple

from shared.config import Config
from shared.agent_client import AgentClient
from shared.telemetry import get_telemetry, init_telemetry
from shared.notifications import NotificationManager
from shared.utils import log_startup_config
from agents.shared.prompts import copy_spec_to_project


logger = logging.getLogger(__name__)


class BaseAgent(abc.ABC):
    """
    Abstract Base Class for autonomous agents.
    """

    def __init__(self, config: Config, agent_client: Optional[AgentClient] = None):
        self.config = config
        self.agent_client = agent_client
        self.notifier = NotificationManager(config)
        self.recent_history: List[str] = []
        self.iteration = 0
        self.consecutive_errors = 0
        self.is_first_run = not config.feature_list_path.exists()
        self.has_run_manager_first = False
        self.start_time = 0.0

    @abc.abstractmethod
    def get_agent_type(self) -> str:
        """Return the agent type string (e.g., 'gemini', 'cursor')."""

    @abc.abstractmethod
    async def run_agent_session(
        self,
        prompt: str,
        status_callback: Optional[Any] = None,
    ) -> Tuple[str, str, List[str]]:
        """
        Run a single agent session and return (status, response_text, executed_actions).
        Status can be 'continue', 'done', 'error'.
        """

    def print_session_header(self, iteration: int, is_first: bool) -> None:
        """Print a visual header for the current session."""
        header = f"  SESSION {iteration} " + (
            "(INITIALIZATION)" if is_first else "(CODING)"
        )
        logger.info("\n" + "=" * 50)
        logger.info(header)
        logger.info("=" * 50 + "\n")

    def log_progress_summary(self) -> None:
        """Log a summary of the current progress from the progress file."""
        progress_file = self.config.progress_file_path
        if progress_file.exists():
            logger.info("Last Progress Update:")
            logger.info("-" * 30)
            try:
                lines = progress_file.read_text().splitlines()
                for line in lines[-10:]:
                    logger.info(line)
            except Exception as e:
                logger.warning(f"Could not read progress file: {e}")
            logger.info("-" * 30 + "\n")

    def select_prompt(self) -> Tuple[str, bool]:
        """Select the appropriate prompt based on configuration and state."""
        # Note: We import prompts here to avoid circular dependencies if any
        from agents.shared.prompts import (
            get_initializer_prompt,
            get_coding_prompt,
            get_manager_prompt,
            get_jira_initializer_prompt,
            get_jira_manager_prompt,
            get_jira_worker_prompt,
            get_qa_prompt,
            get_cleaner_prompt,
        )

        config = self.config
        iteration = self.iteration
        is_first_run = self.is_first_run
        has_run_manager_first = self.has_run_manager_first

        if is_first_run:
            if config.jira and config.jira_ticket_key:
                return get_jira_initializer_prompt(), False
            else:
                return get_initializer_prompt(), False

        # Check for Cleaner Triggers (highest priority post-sign-off)
        if (config.project_dir / "PROJECT_SIGNED_OFF").exists():
            if not (config.project_dir / "cleanup_report.txt").exists():
                logger.info("Project signed off but no cleanup report found. Running Cleaner Agent...")
                return get_cleaner_prompt(), True

        # Check for Manager Triggers
        should_run_manager = False
        manager_trigger_path = config.project_dir / "TRIGGER_MANAGER"
        triggered_by_file = manager_trigger_path.exists()

        if triggered_by_file:
            logger.info("Manager triggered by TRIGGER_MANAGER file.")
            should_run_manager = True
            try:
                manager_trigger_path.unlink()
            except OSError:
                pass
        elif config.run_manager_first and not has_run_manager_first:
            logger.info("Manager triggered by --manager-first flag.")
            should_run_manager = True
            force_manager = True
            self.has_run_manager_first = True
        elif iteration > 0 and iteration % config.manager_frequency == 0:
            logger.info(f"Manager triggered by frequency (Iteration {iteration}).")
            should_run_manager = True

        # Auto-trigger Manager if all features are passing
        if not should_run_manager and config.feature_list_path.exists():
            try:
                features = json.loads(config.feature_list_path.read_text())
                total = len(features)
                passing = sum(1 for f in features if f.get("passes", False))
                if total > 0 and passing == total:
                    logger.info(
                        "All features passed. Triggering Manager for potential sign-off."
                    )
                    should_run_manager = True
            except Exception:
                pass

        # Check for COMPLETED flag
        if not should_run_manager and (config.project_dir / "COMPLETED").exists():
            logger.info(
                "Project marked as COMPLETED but missing SIGN-OFF. Triggering Manager..."
            )
            should_run_manager = True

        if should_run_manager:
            # Check if QA is required before Manager Sign-off
            # We trigger QA if either:
            # 1. Project marked as COMPLETED
            # 2. This is a periodic manager run (not triggered by file or flag)
            force_manager = triggered_by_file or (config.run_manager_first and self.has_run_manager_first)

            is_ready_for_qa = (config.project_dir / "COMPLETED").exists() or (should_run_manager and not force_manager)

            qa_passed_path = config.project_dir / "QA_PASSED"

            if is_ready_for_qa and not qa_passed_path.exists():
                logger.info("Completion signaled. Triggering QA Agent for verification...")
                return get_qa_prompt(), True

            if config.jira and config.jira_ticket_key:
                return get_jira_manager_prompt(), True
            else:
                return get_manager_prompt(), True
        else:
            if config.jira and config.jira_ticket_key:
                return get_jira_worker_prompt(), False
            else:
                return get_coding_prompt(), False

    def inject_jira_context(self, prompt: str) -> str:
        """Inject Jira context into the prompt if applicable."""
        if self.config.jira and self.config.jira_ticket_key:
            if hasattr(self.config, "jira_spec_content") and self.config.jira_spec_content:
                context_to_inject = self.config.jira_spec_content
            else:
                context_to_inject = f"Ticket: {self.config.jira_ticket_key}"

            unique_suffix = self.config.agent_id[-8:] if self.config.agent_id else "default"
            prompt = prompt.replace("{jira_ticket_context}", context_to_inject)
            prompt = prompt.replace("{unique_branch_suffix}", unique_suffix)
        return prompt

    def get_state_file_path(self) -> Path:
        """Return the path to the state persistence file."""
        return self.config.project_dir / ".agent_state.json"

    def save_state(self) -> None:
        """Save the current agent state to a file."""
        state = {
            "iteration": self.iteration,
            "consecutive_errors": self.consecutive_errors,
            "is_first_run": self.is_first_run,
            "has_run_manager_first": self.has_run_manager_first,
            "recent_history": self.recent_history,
        }
        try:
            self.get_state_file_path().write_text(json.dumps(state, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save agent state: {e}")

    def load_state(self) -> None:
        """Load the agent state from a file if it exists."""
        state_path = self.get_state_file_path()
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text())
                self.iteration = state.get("iteration", 0)
                self.consecutive_errors = state.get("consecutive_errors", 0)
                self.is_first_run = state.get("is_first_run", self.is_first_run)
                self.has_run_manager_first = state.get("has_run_manager_first", False)
                self.recent_history = state.get("recent_history", [])
                logger.info(f"Resumed state from {state_path} (Iteration {self.iteration})")
            except Exception as e:
                logger.warning(f"Failed to load agent state: {e}")

    async def _check_control_signals(self) -> bool:
        """Check for stop/pause signals. Returns True if execution should stop."""
        if not self.agent_client:
            return False

        control = self.agent_client.poll_commands()
        if control.stop_requested:
            logger.info("Stop requested by user.")
            self.agent_client.report_state(is_running=False, current_task="Stopped")
            return True

        if control.pause_requested:
            self.agent_client.report_state(current_task="Paused", is_paused=True)
            logger.info("Agent Paused. Waiting for resume...")
            while control.pause_requested:
                await asyncio.sleep(1)
                control = self.agent_client.poll_commands()
                if control.stop_requested:
                    return True
            self.agent_client.report_state(current_task="Resuming...", is_paused=False)
            logger.info("Agent Resumed.")

        return False

    async def _check_completion_signals(self) -> bool:
        """Check for sign-off or human-in-loop. Returns True if execution should stop."""
        # Check for Sign-off
        if (self.config.project_dir / "PROJECT_SIGNED_OFF").exists():
            logger.info("\n" + "=" * 50)
            logger.info("  PROJECT SIGNED OFF")
            logger.info("=" * 50)
            self.notifier.notify("project_completion", f"Project {self.config.project_dir.name} has been signed off and completed.")

            # Jira Status Transition
            if self.config.jira and self.config.jira_ticket_key:
                from shared.workflow import complete_jira_ticket
                await complete_jira_ticket(self.config)

            # Only stop if cleanup is also done (standardised flow)
            if (self.config.project_dir / "cleanup_report.txt").exists():
                return True
            else:
                logger.info("Project signed off. Continuing for final cleanup...")
                return False

        # Check for Human in Loop
        human_loop_file = self.config.project_dir / "human_in_loop.txt"
        if human_loop_file.exists():
            try:
                reason = human_loop_file.read_text().strip()
                logger.info("\n" + "=" * 50)
                logger.info("  HUMAN IN LOOP REQUESTED")
                logger.info("=" * 50)
                logger.info(f"Reason: {reason}")

                self.notifier.notify("human_in_loop", f"Human intervention requested: {reason}")

                if self.agent_client:
                    self.agent_client.report_state(
                        is_running=False,
                        current_task=f"Stopped: Human in Loop ({reason})",
                    )
                return True
            except Exception as e:
                logger.error(f"Error reading human_in_loop.txt: {e}")

        return False

    async def _handle_session_result(self, status: str, response: str, new_actions: List[str], iter_start_time: float, using_manager: bool) -> None:
        """Handle the result of the session."""
        if status in ("continue", "done"):
            self.consecutive_errors = 0
            self.is_first_run = False  # Successful run

            # Notifications
            if using_manager:
                self.notifier.notify("manager", f"Manager Update (Iteration {self.iteration}):\n{response[:500]}...")
            else:
                self.notifier.notify("iteration", f"Iteration {self.iteration} complete.\nActions: {len(new_actions)}")

            if self.agent_client:
                self.agent_client.report_state(current_task="Waiting (Auto-Continue)")

            logger.info(f"Agent will auto-continue in {self.config.auto_continue_delay}s...")
            self.log_progress_summary()
            self.save_state()

            # Telemetry: Record Iteration Duration
            get_telemetry().record_gauge(
                "iteration_duration_seconds", time.time() - iter_start_time
            )

            if status == "done":
                logger.info("Agent signaled completion.")

            # Interruptible sleep
            sleep_steps = int(self.config.auto_continue_delay * 10)
            for _ in range(sleep_steps):
                await asyncio.sleep(0.1)
                # Check interruption
                if self.agent_client and self.agent_client.poll_commands().stop_requested:
                    break

        elif status == "error":
            self.consecutive_errors += 1
            logger.error(
                f"Session encountered an error (Attempt {self.consecutive_errors}/{self.config.max_consecutive_errors})."
            )

            self.notifier.notify("error", f"Agent encountered error: {response}")
            self.save_state()

            logger.info("Retrying in 10 seconds...")
            await asyncio.sleep(10)

    async def _execute_iteration(self, iter_start_time: float) -> None:
        """Execute a single iteration of the agent loop."""
        self.print_session_header(self.iteration, self.is_first_run)

        # Choose prompt
        prompt, using_manager = self.select_prompt()

        # Inject Jira Context
        prompt = self.inject_jira_context(prompt)

        # Run session
        if self.agent_client:
            self.agent_client.report_state(
                current_task=f"Executing {'Manager' if using_manager else 'Agent'}"
            )

        original_model = self.config.model
        if using_manager and self.config.manager_model:
            self.config.model = self.config.manager_model
            logger.info(f"Switched to Manager Model: {self.config.model}")

        # Status Callback Handler
        current_turn_log = []

        def status_update(current_task=None, output_line=None):
            if not self.agent_client:
                return

            updates = {}
            if current_task:
                updates["current_task"] = current_task

            if output_line:
                clean_line = output_line.rstrip()
                if clean_line:
                    current_turn_log.append(clean_line)
                    updates["last_log"] = current_turn_log[-30:]

            if updates:
                self.agent_client.report_state(**updates)

        status, response, new_actions = await self.run_agent_session(
            prompt,
            status_callback=status_update,
        )

        if using_manager and self.config.manager_model:
            self.config.model = original_model
            logger.info(f"Restored Agent Model: {self.config.model}")

        if new_actions:
            self.recent_history.extend(new_actions)
            self.recent_history = self.recent_history[-10:]  # Keep last 10 actions
            if self.agent_client:
                self.agent_client.report_state(last_log=[str(a) for a in self.recent_history])

        await self._handle_session_result(status, response, new_actions, iter_start_time, using_manager)

    async def run_autonomous_loop(self) -> None:
        """
        Run the autonomous agent loop.
        """
        log_startup_config(self.config, logger)

        # Ensure project directory exists
        self.config.project_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Telemetry
        service_name = f"{self.get_agent_type()}_agent"
        if self.agent_client:
            service_name = self.agent_client.agent_id

        init_telemetry(
            service_name, agent_type=self.get_agent_type(), project_name=self.config.project_dir.name
        )
        get_telemetry().start_system_monitoring()
        get_telemetry().capture_logs_from("agents")

        # Notify Start
        self.notifier.notify("agent_start", f"{self.get_agent_type().capitalize()} Agent started for project {self.config.project_dir.name}")

        # Try to resume state
        self.load_state()

        # Initialize Project (Copy Spec if first run)
        if self.is_first_run:
            logger.info("Fresh start - copying spec to project")
            copy_spec_to_project(self.config.project_dir, self.config.spec_file)
            # Cleanup any stale signals
            for sig in ["COMPLETED", "QA_PASSED", "PROJECT_SIGNED_OFF"]:
                sig_path = self.config.project_dir / sig
                if sig_path.exists():
                    try:
                        sig_path.unlink()
                    except OSError:
                        pass
        else:
            logger.info("Continuing existing project")
            self.log_progress_summary()

        self.start_time = time.time()

        # Initial Status
        if self.agent_client:
            self.agent_client.report_state(
                current_task="Initializing", is_running=True, start_time=self.start_time
            )

        # Main Loop
        while True:
            iter_start_time = time.time()

            # Check Limits
            if self.config.max_iterations is not None and self.iteration >= self.config.max_iterations:
                # Safety: If project is signed off but cleanup is pending, we allow a few extra turns
                is_signed_off = (self.config.project_dir / "PROJECT_SIGNED_OFF").exists()
                cleanup_done = (self.config.project_dir / "cleanup_report.txt").exists()

                if is_signed_off and not cleanup_done and self.iteration < (self.config.max_iterations + 5):
                    logger.info(f"Max iterations reached, but cleanup is pending. Allowing extra turn {self.iteration + 1}...")
                else:
                    logger.info("Max iterations reached. Stopping.")
                    break

            # Check Control Signals
            if await self._check_control_signals():
                break

            if self.agent_client and self.agent_client.local_control.skip_requested:
                self.agent_client.clear_skip()
                logger.info("Skipping iteration as requested.")
                continue

            self.iteration += 1
            # Update State
            if self.agent_client:
                self.agent_client.report_state(
                    iteration=self.iteration, current_task="Preparing Prompt"
                )

            # Telemetry: Record Iteration
            get_telemetry().record_gauge("agent_iteration", self.iteration)
            get_telemetry().increment_counter("agent_iterations_total")

            # Check Signals
            if await self._check_completion_signals():
                break

            # Execute
            await self._execute_iteration(iter_start_time)

            # Check Error Limit
            if self.consecutive_errors >= self.config.max_consecutive_errors:
                logger.critical(
                    f"Too many consecutive errors ({self.config.max_consecutive_errors}). Stopping execution."
                )
                break

            # Prepare next session
            if self.config.max_iterations is None or self.iteration < self.config.max_iterations:
                logger.debug("Preparing next session...")
                await asyncio.sleep(1)

        logger.info("\n" + "=" * 50)
        logger.info("  SESSION COMPLETE")
        logger.info("=" * 50)

        self.notifier.notify("agent_stop", f"{self.get_agent_type().capitalize()} Agent stopped for project {self.config.project_dir.name}")

        if self.agent_client:
            self.agent_client.report_state(is_running=False, current_task="Completed")
