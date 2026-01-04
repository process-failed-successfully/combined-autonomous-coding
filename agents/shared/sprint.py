import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from shared.config import Config
from shared.agent_client import AgentClient
from shared.notifications import NotificationManager
from shared.telemetry import get_telemetry, init_telemetry
from agents.gemini.client import GeminiClient
from agents.shared.prompts import get_sprint_planner_prompt, get_sprint_coding_prompt, get_initializer_prompt
from agents.gemini.agent import run_agent_session as run_gemini_session, GeminiAgent
from agents.shared.base_agent import BaseAgent
from agents.openrouter.client import OpenRouterClient
from agents.openrouter.agent import run_agent_session as run_openrouter_session
from agents.local.client import LocalClient
import shutil
from agents.local.agent import run_agent_session as run_local_session
from agents.shared.worktree_manager import WorktreeManager

# Lazy import or dynamic import to avoid circular dep if possible,
# but for now explicit import is fine if structure allows.
# We need to import Cursor logic.
# Assuming agents.cursor package exists and has similar structure.
# We use a try-except block to avoid hard crash if cursor module is missing in some envs,
# though here we know it exists.
try:
    from agents.cursor.agent import (
        run_agent_session as run_cursor_session,
        CursorClient,
    )
except ImportError:
    run_cursor_session = None  # type: ignore
    CursorClient = None  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class Task:
    id: str
    title: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, FAILED, BLOCKED
    assigned_agent: Optional[str] = None
    agent_output: str = ""
    feature_name: Optional[str] = None


@dataclass
class SprintPlan:
    sprint_goal: str
    tasks: List[Task]



def detect_runaway(text: str) -> bool:
    """Detects if text contains excessive repetition of phrases."""
    if not text or len(text) < 100:
        return False
        
    words = text.split()
    if len(words) < 20:
        return False
        
    # Check for repeated sequences
    # Simple heuristic: if the set of unique words is very small compared to length
    unique_ratio = len(set(words)) / len(words)
    if unique_ratio < 0.1: # e.g. 100 words, only 10 unique
         return True
         
    # Check for direct phrase repetition (e.g. "foo bar foo bar foo bar")
    # Taking chunks of 5 words
    chunk_size = 5
    if len(words) > chunk_size * 4:
         chunk = tuple(words[:chunk_size])
         repeats = 0
         for i in range(0, len(words) - chunk_size, chunk_size):
             if tuple(words[i:i+chunk_size]) == chunk:
                 repeats += 1
         if repeats > 5 and repeats > len(words) / (chunk_size * 1.5):
             return True
             
    return False

class SprintManager:
    def __init__(self, config: Config, agent_client=None):
        self.config = config
        self.agent_client = agent_client
        self.notifier = NotificationManager(config)
        self.plan: Optional[SprintPlan] = None
        self.tasks_by_id: Dict[str, Task] = {}
        self.running_tasks: Set[str] = set()
        self.worktree_manager = WorktreeManager(config.project_dir)

        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        self.rescued_tasks: Set[str] = set() # Tasks that failed but work was saved

    def _get_agent_runner(self, config: Optional[Config] = None):
        cfg = config or self.config
        if cfg.agent_type == "cursor":
            if CursorClient is None:
                raise ValueError("Cursor Agent not available (ImportError).")
            return CursorClient(cfg), run_cursor_session
        elif cfg.agent_type == "openrouter":
            return OpenRouterClient(cfg), run_openrouter_session
        elif cfg.agent_type == "local":
            return LocalClient(cfg), run_local_session
        else:
            return GeminiClient(cfg), run_gemini_session

    async def run_planning_phase(self):
        """Runs the Lead Agent to create the sprint plan."""
        logger.info("Starting Sprint Planning Phase...")
        start_time = time.time()

        if self.agent_client:
            self.agent_client.report_state(current_task="Sprint Planning")

        # Notify Start
        self.notifier.notify("sprint_start", f"Sprint Planning started for project {self.config.project_dir.name}")

        client, session_runner = self._get_agent_runner()

        # specific prompt for planning
        # specific prompt for planning
        base_prompt = get_sprint_planner_prompt()

        # Check for app_spec or initial goal
        spec_path = self.config.project_dir / "app_spec.txt"
        goal_text = "See app_spec.txt or README.md"
        if spec_path.exists():
            goal_text = spec_path.read_text()

        # Check for feature list
        feature_list_content = "No feature_list.json found."
        if self.config.feature_list_path.exists():
            feature_list_content = self.config.feature_list_path.read_text()
            logger.info(f"Loaded feature list from {self.config.feature_list_path}")

        dind_context = ""
        if self.config.dind_enabled:
            dind_context = "- **Docker-in-Docker:** You have access to the Docker socket. You can launch additional containers (e.g., using `docker run` or `docker-compose`) for testing purposes if required."

        prompt = base_prompt.format(
            working_directory=self.config.project_dir,
            user_goal=goal_text,
            feature_list_content=feature_list_content,
            dind_context=dind_context,
        )

        # Run session
        # We use run_agent_session but we expect a write:sprint_plan.json
        status, response, actions = await session_runner(client, prompt)

        # Check if plan file exists
        search_path = self.config.project_dir / "sprint_plan.json"

        if not search_path.exists():
            logger.warning(
                "sprint_plan.json file not found. Attempting to parse from response text..."
            )
            # Fallback: parsing from code block
            # Looking for ```json or ```write:sprint_plan.json blocks
            import re

            # Simple regex to find the json block
            # Match ```json ... ``` OR ```write:sprint_plan.json ... ```
            # We just want the content inside
            json_pattern = r"```(?:json|write:sprint_plan\.json)\n([\s\S]*?)\n```"
            match = re.search(json_pattern, response)

            if match:
                try:
                    json_content = match.group(1)
                    search_path.write_text(
                        json_content
                    )  # Write it to file for consistency
                    logger.info(
                        "Successfully recovered sprint plan from response text."
                    )
                except Exception as e:
                    logger.error(f"Failed to extract plan from response: {e}")
                    get_telemetry().record_gauge(
                        "sprint_planning_duration_seconds",
                        time.time() - start_time,
                        labels={"status": "fail"}
                    )
                    return False
            else:
                logger.error(
                    "Sprint Plan not created and no JSON block found. Aborting."
                )
                logger.debug(f"Full response:\n{response}")
                get_telemetry().record_gauge(
                    "sprint_planning_duration_seconds",
                    time.time() - start_time,
                    labels={"status": "fail"}
                )
                return False

        try:
            plan_data = json.loads(search_path.read_text())
            tasks = []
            for t in plan_data.get("tasks", []):
                tasks.append(
                    Task(
                        id=t["id"],
                        title=t.get("title", "No Title"),
                        description=t.get("description", ""),
                        dependencies=t.get("dependencies", []),
                        feature_name=t.get("feature_name"),
                    )
                )
            self.plan = SprintPlan(
                sprint_goal=plan_data.get("sprint_goal", ""), tasks=tasks
            )
            self.tasks_by_id = {t.id: t for t in tasks}
            logger.info(f"Sprint Plan Created: {len(tasks)} tasks.")

            get_telemetry().record_gauge(
                "sprint_planning_duration_seconds",
                time.time() - start_time,
                labels={"status": "success"}
            )
            get_telemetry().record_gauge("sprint_tasks_total", len(tasks))

            return True
        except Exception as e:
            logger.exception(f"Failed to parse sprint plan: {e}")
            get_telemetry().record_gauge(
                "sprint_planning_duration_seconds",
                time.time() - start_time,
                labels={"status": "fail"}
            )
            return False

    async def run_worker(self, task: Task):
        """Runs a worker agent on a specific task."""
        logger.info(f"SPAWNING WORKER for Task {task.id}: {task.title}")
        start_time = time.time()

        if self.agent_client:
            self.agent_client.report_state(
                current_task=f"Spawning Worker: {task.title}"
            )

        task.status = "IN_PROGRESS"

        # Increment active workers
        get_telemetry().record_gauge(
            "sprint_active_workers",
            len(self.running_tasks) + 1  # running_tasks includes this one, set by caller but let's be safe.
            # Actually caller adds to self.running_tasks before calling run_worker.
            # So len(self.running_tasks) is correct.
        )
        # But wait, self.running_tasks is a set on the manager instance.
        # Accessing it here is fine as it's async and single threaded (mostly).
        # However, to be cleaner, we can just increment a counter or re-set the gauge based on set size.
        # Let's rely on update loop to set the gauge or set it here.
        # Simpler: just set it based on current set size.
        get_telemetry().record_gauge("sprint_active_workers", len(self.running_tasks))

        # Create a specific config for this worker?
        # We share the main config but maybe we want separate logs?
        # For now, share config. Logging might get interleaved.
        # TODO: Thread-safe logging context?
        
        # 1. Isolation: Create Worktree
        worktree_path = self.worktree_manager.create_worktree(task.id)
        if not worktree_path:
             logger.error(f"Failed to create worktree for {task.id}. Aborting")
             task.status = "FAILED"
             self.failed_tasks.add(task.id)
             self.running_tasks.remove(task.id)
             return

        # 1.5 Context Copy
        # Copy critical context files that might not be in git or have local changes
        for filename in ["feature_list.json", "sprint_plan.json"]:
             src = self.config.project_dir / filename
             dst = worktree_path / filename
             if src.exists():
                 try:
                     shutil.copy(src, dst)
                 except Exception as e:
                     logger.warning(f"Failed to copy {filename} to worktree: {e}")

        # 2. Config Clone
        # We need a shallow copy of config with updated project_dir
        # Config is a dataclass, so replace() works if we were using it, but it's not frozen?
        # It's a regular dataclass.
        import copy
        worker_config = copy.copy(self.config)
        worker_config.project_dir = worktree_path
        # Also need detailed update of paths derived from project_dir?
        # NO, Config properties work dynamically based on project_dir.
        # BUT feature_list_path is a property, good.
        # However, what about initial files?
        # If worktree is created, it has the files.
        # BUT if the main repo has `app_spec.txt`, the worktree will too.
        
        # Note: We must NOT pass the main self.config to the worker logic if it relies on path.
        # We assume _get_agent_runner uses the passed config or we need to instantiate new clients?
        # _get_agent_runner uses self.config. We need to pass the new config.
        # Refactor _get_agent_runner to accept config?
        # Or just instantiate client here.
        
        client, session_runner = self._get_agent_runner(worker_config)

        # Instantiate a dedicated AgentClient for this worker
        from shared.utils import generate_agent_id

        # Read spec content for ID generation consistency
        spec_content = ""
        # Use worker_config to read from worktree
        if worker_config.spec_file and worker_config.spec_file.exists():
            spec_content = worker_config.spec_file.read_text()
        
        # Or fallback to main config if file missing in worktree (shouldn't happen)
        
        # Base ID on hash
        base_id = generate_agent_id(
            worker_config.project_dir.name, spec_content, "worker"
        )
        worker_id = (
            f"{base_id}-{task.id}"
        )

        dashboard_url = "http://localhost:7654"
        if self.agent_client:
            dashboard_url = self.agent_client.dashboard_url

        worker_client = AgentClient(agent_id=worker_id, dashboard_url=dashboard_url)
        worker_client.report_state(
            is_running=True,
            current_task=f"Starting Task: {task.title}",
            iteration=0,
        )

        # Runner already selected above using worker_config
        base_prompt = get_sprint_coding_prompt()

        dind_context = ""
        if worker_config.dind_enabled:
            dind_context = "- **Docker-in-Docker:** You have access to the Docker socket. You can launch additional containers (e.g., using `docker run` or `docker-compose`) for testing purposes if required."

        # Explicit string replacement for robust prompt
        formatted_prompt = base_prompt.replace("{task_id}", task.id)
        formatted_prompt = formatted_prompt.replace("{task_title}", task.title)
        formatted_prompt = formatted_prompt.replace("{task_description}", task.description)
        # Note: coding_prompt uses {dind_context} if we kept it, but robust prompt might not have {working_directory} in the same way.
        # Let's check prompt structure. Our new prompt has {dind_context} but uses `pwd` for working dir.
        formatted_prompt = formatted_prompt.replace("{dind_context}", dind_context)

        history: List[str] = []
        max_turns = 10  # Cap turns per task
        turns = 0
        last_actions: List[str] = []
        last_response: str = ""
        repetition_count = 0

        try:
            while turns < max_turns:
                turns += 1
                worker_client.report_state(
                    iteration=turns, current_task=f"Executing: {task.title}"
                )

                # Check for pause
                ctl = worker_client.poll_commands()
                if ctl.pause_requested:
                    worker_client.report_state(is_paused=True, current_task="Paused")
                    while worker_client.poll_commands().pause_requested:
                        await asyncio.sleep(1)
                    worker_client.report_state(is_paused=False)

                # Status callback for real-time updates
                # We assume session_runner supports status_callback (Gemini and
                # Cursor now both do)
                current_turn_log = []

                def status_update(current_task=None, output_line=None):
                    updates = {}
                    if current_task:
                        updates["current_task"] = current_task

                    if output_line:
                        clean_line = output_line.rstrip()
                        if clean_line:
                            current_turn_log.append(clean_line)
                            # Show last 10 lines
                            updates["last_log"] = current_turn_log[-10:]

                    if updates:
                        worker_client.report_state(**updates)
                status, response, actions = await session_runner(
                    client, formatted_prompt, history, status_callback=status_update
                )

                # 1. Runaway Output Check
                if detect_runaway(response):
                    logger.error(f"Task {task.id}: Runaway output detected.")
                    task.status = "FAILED"
                    self.failed_tasks.add(task.id)
                    self.running_tasks.remove(task.id)
                    
                    worker_client.report_state(current_task="Failed: Runaway Output", is_running=False)
                    worker_client.stop()
                    
                    # Rescue
                    if self.worktree_manager.rescue_worktree(task.id):
                        self.rescued_tasks.add(task.id)
                        logger.info(f"Work rescued for task {task.id} on branch sprint/task-{task.id}")
                        self.worktree_manager.cleanup_worktree(task.id, delete_branch=False)
                        self.worktree_manager.cleanup_worktree(task.id, delete_branch=False)
                    else:
                        self.worktree_manager.cleanup_worktree(task.id, delete_branch=True)
                    return

                # 2. Loop Detection Guardrail (Actions OR Text Loop)
                is_loop = False
                
                # Action Loop
                if actions and actions == last_actions:
                    is_loop = True
                # Text Loop (only if no actions)
                elif not actions and response and response == last_response:
                    is_loop = True
                
                if is_loop:
                    repetition_count += 1
                    logger.warning(f"Task {task.id}: Repetitive behavior detected ({repetition_count}/3).")
                    if repetition_count >= 3:
                        logger.error(f"Task {task.id}: Repetition loop detected. Terminating.")
                        task.status = "FAILED"
                        self.failed_tasks.add(task.id)
                        self.running_tasks.remove(task.id)

                        # Metrics
                        duration = time.time() - start_time
                        get_telemetry().increment_counter("sprint_tasks_failed")
                        get_telemetry().record_histogram("sprint_task_duration_seconds", duration, labels={"status": "repetition_loop"})
                        get_telemetry().record_gauge("sprint_active_workers", len(self.running_tasks))

                        worker_client.report_state(current_task="Failed: Repetition Loop", is_running=False)
                        worker_client.stop()
                        
                        # Rescue
                        if self.worktree_manager.rescue_worktree(task.id):
                            self.rescued_tasks.add(task.id)
                            logger.info(f"Work rescued for task {task.id} on branch sprint/task-{task.id}")
                            self.worktree_manager.cleanup_worktree(task.id, delete_branch=False)
                        else:
                            self.worktree_manager.cleanup_worktree(task.id, delete_branch=True)
                        return
                else:
                    if actions or (response != last_response):
                        repetition_count = 0
                        last_actions = actions
                        last_response = response

                # Report recent history
                if actions:
                    worker_client.report_state(last_log=actions)

                # Check for completion signal
                if "SPRINT_TASK_COMPLETE" in response:
                    logger.info(f"Task {task.id} Completed.")
                    task.status = "COMPLETED"
                    self.completed_tasks.add(task.id)
                    self.running_tasks.remove(task.id)

                    # Metrics
                    duration = time.time() - start_time
                    get_telemetry().increment_counter("sprint_tasks_completed")
                    get_telemetry().record_histogram("sprint_task_duration_seconds", duration, labels={"status": "success"})
                    get_telemetry().record_gauge("sprint_active_workers", len(self.running_tasks))

                    self.notifier.notify("sprint_task_complete", f"Task Completed: {task.title}")

                    worker_client.report_state(
                        current_task="Completed", is_running=False
                    )
                    worker_client.stop()
                    
                    # Merge Logic
                    merged = self.worktree_manager.merge_worktree(task.id)
                    if merged:
                         logger.info(f"Task {task.id} merged successfully.")
                         self.worktree_manager.cleanup_worktree(task.id)
                    else:
                         logger.error(f"Task {task.id} FAILED TO MERGE. Marking as failed, but PRESERVING BRANCH.")

                         task.status = "FAILED"
                         self.failed_tasks.add(task.id)
                         self.running_tasks.remove(task.id)
                         self.completed_tasks.remove(task.id) 

                         # Metrics
                         get_telemetry().increment_counter("sprint_tasks_failed", labels={"reason": "merge_conflict"})

                         # Notify User
                         self.notifier.notify(
                             "sprint_merge_failed",
                             f"Task {task.title} ({task.id}) failed to merge. Branch preserved."
                         )

                         # Cleanup worktree but KEEP BRANCH for manual merge
                         self.worktree_manager.cleanup_worktree(task.id, delete_branch=False)
                         return

                    return

                if "SPRINT_TASK_FAILED" in response:
                    logger.error(f"Task {task.id} Failed by Agent.")
                    task.status = "FAILED"
                    self.failed_tasks.add(task.id)
                    self.running_tasks.remove(task.id)

                    # Metrics
                    duration = time.time() - start_time
                    get_telemetry().increment_counter("sprint_tasks_failed")
                    get_telemetry().record_histogram("sprint_task_duration_seconds", duration, labels={"status": "agent_failed"})
                    get_telemetry().record_gauge("sprint_active_workers", len(self.running_tasks))

                    worker_client.report_state(current_task="Failed", is_running=False)
                    worker_client.stop()
                    
                    # Rescue
                    if self.worktree_manager.rescue_worktree(task.id):
                        self.rescued_tasks.add(task.id)
                        logger.info(f"Work rescued for task {task.id} on branch sprint/task-{task.id}")
                        self.worktree_manager.cleanup_worktree(task.id, delete_branch=False)
                    else:
                        self.worktree_manager.cleanup_worktree(task.id, delete_branch=True)
                    return

                if status == "error":
                    logger.error(f"Task {task.id} errored underneath.")
                    # Retry?

                # Append actions to history for context
                if actions:
                    history.extend(actions)
                    history = history[-5:]
                elif response:
                    # If no actions, capture the response text to avoid amnesia loops
                    # We truncate to avoid polluting context too much, but enough to show what was said.
                    history.append(f"[Response]: {response[:200]}...")
                    history = history[-5:]

            # If max turns reached
            logger.warning(f"Task {task.id} timed out (max turns).")
            task.status = "FAILED"
            self.failed_tasks.add(task.id)
            self.running_tasks.remove(task.id)

            # Metrics
            duration = time.time() - start_time
            get_telemetry().increment_counter("sprint_tasks_failed")
            get_telemetry().record_histogram("sprint_task_duration_seconds", duration, labels={"status": "timeout"})
            get_telemetry().record_gauge("sprint_active_workers", len(self.running_tasks))

            worker_client.report_state(current_task="Timed Out", is_running=False)
            worker_client.stop()
            
            # Rescue
            if self.worktree_manager.rescue_worktree(task.id):
                self.rescued_tasks.add(task.id)
                logger.info(f"Work rescued for task {task.id} on branch sprint/task-{task.id}")
                self.worktree_manager.cleanup_worktree(task.id, delete_branch=False)
            else:
                 self.worktree_manager.cleanup_worktree(task.id, delete_branch=True)

        except Exception as e:
            logger.exception(f"Worker {task.id} crashed: {e}")
            worker_client.report_state(current_task=f"Crashed: {e}", is_running=False)

            # Metrics
            duration = time.time() - start_time
            get_telemetry().increment_counter("sprint_tasks_failed")
            get_telemetry().record_histogram("sprint_task_duration_seconds", duration, labels={"status": "crashed"})
            get_telemetry().record_gauge("sprint_active_workers", len(self.running_tasks))

            worker_client.stop()
            
            # Rescue
            if self.worktree_manager.rescue_worktree(task.id):
                self.rescued_tasks.add(task.id)
                logger.info(f"Work rescued for task {task.id} on branch sprint/task-{task.id}")
                self.worktree_manager.cleanup_worktree(task.id, delete_branch=False)
            else:
                 self.worktree_manager.cleanup_worktree(task.id, delete_branch=True)

    async def execute_sprint(self):
        """Main execution loop."""
        iteration = 0
        while len(self.completed_tasks) + len(self.failed_tasks) < len(self.plan.tasks):
            iteration += 1
            if self.agent_client:
                self.agent_client.report_state(iteration=iteration)

            # Check for runnable tasks
            runnable = []
            for task in self.plan.tasks:
                if task.status in ["PENDING", "BLOCKED"]:
                    # Check dependencies
                    deps_met = all(d in self.completed_tasks for d in task.dependencies)
                    if deps_met:
                        runnable.append(task)
                        # Reset status to PENDING so it can be picked up,
                        # though we add to runnable directly
                        if task.status == "BLOCKED":
                            task.status = "PENDING"
                    else:
                        task.status = "BLOCKED"

            # Mark blocked tasks as pending if deps become met?
            # Actually above logic handles it: PENDING -> checks deps -> if unmet stays PENDING (or effectively blocked)
            # Just listing runnable ones is enough.

            # Launch tasks up to limit
            free_slots = self.config.max_agents - len(self.running_tasks)

            to_launch = runnable[:free_slots]

            for task in to_launch:
                self.running_tasks.add(task.id)
                task.status = "IN_PROGRESS"
                asyncio.create_task(self.run_worker(task))

            if (
                not self.running_tasks
                and not runnable
                and len(self.completed_tasks) < len(self.plan.tasks)
            ):
                logger.error(
                    "Deadlock detected? No running tasks and no runnable tasks."
                )
                break

            await asyncio.sleep(1)  # Yield execution

    def update_feature_list(self):
        """Checks completed tasks and updates feature_list.json."""
        if not self.config.feature_list_path.exists():
            return

        try:
            features = json.loads(self.config.feature_list_path.read_text())
        except Exception as e:
            logger.error(f"Failed to read feature list: {e}")
            return

        # Map: Feature Name -> List of Task Statuses
        # We need to consider that the plan might NOT contain all tasks for a feature if it's large.
        # But for now, we assume if ALL tasks in the *current plan* for a feature are done,
        # we mark it as done? No, that's risky.
        # Prudent approach: The Planner creates tasks for a feature. If all those tasks succeed,
        # we can toggle the feature status?
        # A better approach: The feature status in JSON tracks overall progress.
        # We mark it as 'completed' only if all planned tasks for it are done.

        # Determine which features were present in this plan
        planned_features = set()
        for t in self.plan.tasks:
            if t.feature_name:
                planned_features.add(t.feature_name)

        if not planned_features:
            return

        updated_any = False
        for feature in features:
            f_name = feature.get("name")  # Assuming 'name' key provided by user or standard?
            # Or assume list of strings? No, prompted as JSON in previous step, usually list of objects.
            # But earlier code used `feature.get("name")` in test... wait, test used name.
            # Let's assume standard object structure or check prompt.
            # Prompt doesn't enforce feature list structure, but it consumes it.
            # Assuming list of dicts with "name" or just keys.

            if f_name in planned_features:
                # Check if ALL tasks for this feature in the CURRENT plan are completed
                tasks_for_feature = [t for t in self.plan.tasks if t.feature_name == f_name]
                if tasks_for_feature:
                    all_done = all(t.status == "COMPLETED" for t in tasks_for_feature)
                    if all_done:
                        if feature.get("status") != "completed":
                            feature["status"] = "completed"
                            updated_any = True
                            logger.info(f"Marking feature '{f_name}' as COMPLETED in feature_list.json")

        if updated_any:
            self.config.feature_list_path.write_text(json.dumps(features, indent=2))

    async def run_post_sprint_checks(self):
        """Runs Manager and optional QA agents after sprint execution."""
        logger.info("Running Post-Sprint Manager Review...")
        
        # We can reuse the GeminiAgent logic but simplified.
        # We need a 'Manager' agent instance.
        
        # 1. Manager (checks progress, successes, etc)
        # We create a temporary config for the manager
        manager_config = self.config
        
        # Use GeminiAgent as it wraps BaseAgent logic which handles prompts
        # But BaseAgent loop is infinite. We just want one check.
        # So we can use run_agent_session directly with Manager prompt?
        # Better: Instantiate GeminiAgent and call a specific method or just use session runner with Manager prompt.
        
        from agents.shared.prompts import get_manager_prompt, get_qa_prompt
        
        # Get Manager Prompt
        manager_prompt = get_manager_prompt()
        
        # Inject context (same as BaseAgent)
        if self.config.jira and self.config.jira_ticket_key:
             # If Jira, usage might differ, but for now stick to standard manager
             pass

        # Run Manager Session
        client, session_runner = self._get_agent_runner()
        # We need to construct the prompt with context like BaseAgent does, but simpler?
        # BaseAgent relies on 'get_file_tree' injected inside run_agent_session.
        # So we just pass the raw prompt.
        
        logger.info("  -> Invoking Manager Agent...")
        status, response, actions = await session_runner(client, manager_prompt)
        
        if actions:
             logger.info(f"Manager performed actions: {len(actions)}")
             
        # Check if Manager marked it as COMPLETED or if it was already COMPLETED
        if (self.config.project_dir / "COMPLETED").exists():
            if not (self.config.project_dir / "QA_PASSED").exists():
                 logger.info("Project marked COMPLETED. Running QA Agent...")
                 qa_prompt = get_qa_prompt()
                 status, response, actions = await session_runner(client, qa_prompt)
                 if (self.config.project_dir / "QA_PASSED").exists():
                     logger.info("QA Passed!")
                 else:
                     logger.info("QA did not pass yet.")
            else:
                 logger.info("Project COMPLETED and QA PASSED.")
    async def ensure_project_initialized(self):
        """Ensures the project has a valid feature_list.json. If not, runs initialization."""
        needs_init = False
        if not self.config.feature_list_path.exists():
            needs_init = True
        else:
            try:
                content = self.config.feature_list_path.read_text().strip()
                if not content:
                    needs_init = True
                else:
                    data = json.loads(content)
                    if not isinstance(data, list) or not data:
                        needs_init = True
            except Exception:
                needs_init = True

        if needs_init:
            logger.info("Project uninitialized or feature list invalid. Running Initializer Agent...")
            
            client, session_runner = self._get_agent_runner()
            prompt = get_initializer_prompt()
            
            # Inject Specs
            spec_path = self.config.project_dir / "app_spec.txt"
            goal_text = "See app_spec.txt or README.md"
            if spec_path.exists():
                goal_text = spec_path.read_text()
            
            # Simple Injection similar to BaseAgent?
            # get_initializer_prompt usually expects formatting or context injection?
            # Checking BaseAgent.select_prompt -> just calls get_initializer_prompt().
            # and run_agent_session injects "CURRENT CONTEXT".
            # So we can just run it.
            
            status, response, actions = await session_runner(client, prompt)
            
            if self.config.feature_list_path.exists() and self.config.feature_list_path.stat().st_size > 0:
                logger.info("Initialization Complete. Feature list created.")
            else:
                logger.error("Initialization Failed. Feature list still missing.")



async def run_single_sprint(config: Config, agent_client=None) -> int:
    manager = SprintManager(config, agent_client)

    # 1. Plan
    success = await manager.run_planning_phase()
    if not success:
        return 0

    if not manager.plan or not manager.plan.tasks:
        return 0

    # 2. Execute
    await manager.execute_sprint()

    # 3. Validation / Feature Update
    # 3. Update Feature List based on Task Completion
    manager.update_feature_list()

    # 4. Post-Sprint Checks (Manager + QA)
    await manager.run_post_sprint_checks()

    logger.info("Sprint Completed.")
    manager.notifier.notify(
        "sprint_complete",
        f"Sprint Completed for project {config.project_dir.name}. {len(manager.completed_tasks)} tasks finished.",
    )

    return len(manager.plan.tasks)


async def run_sprint(config: Config, agent_client=None):
    # Initialize telemetry for sprint mode as it might be the entry point
    init_telemetry(
        service_name="sprint_manager",
        agent_type="sprint",
        project_name=config.project_dir.name
    )

    manager = SprintManager(config, agent_client)
    await manager.ensure_project_initialized()

    logger.info("Starting Continuous Sprint Mode.")
    iteration = 0

    while True:
        iteration += 1
        logger.info(f"--- Starting Sprint Cycle {iteration} ---")

        task_count = await run_single_sprint(config, agent_client)

        if task_count == 0:
            logger.info(
                "Sprint Plan is empty. All features assumed complete. Exiting Sprint Mode."
            )
            break

        logger.info(
            f"Sprint Cycle {iteration} finished with {task_count} tasks planned. Proceeding to next cycle..."
        )
        await asyncio.sleep(2)
