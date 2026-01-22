import os
import sys
from pathlib import Path
import shutil
import subprocess
import json
from datetime import datetime
from typing import Optional
import re
from shared.charts import draw_ascii_bar_chart

WORKFLOW_STAGES = {
    "IN_PROGRESS": {"name": "In Progress", "file": None},
    "COMPLETED": {"name": "Completed", "file": "COMPLETED"},
    "QA_PASSED": {"name": "QA Passed", "file": "QA_PASSED"},
    "SIGNED_OFF": {"name": "Signed Off", "file": "PROJECT_SIGNED_OFF"},
}

# Ordered list of stages for advancing/reverting
WORKFLOW_ORDER = ["IN_PROGRESS", "COMPLETED", "QA_PASSED", "SIGNED_OFF"]


def get_workflow_stage(project_dir: Path):
    """Determines the current workflow stage by checking for marker files."""
    if (project_dir / WORKFLOW_STAGES["SIGNED_OFF"]["file"]).exists():
        return "SIGNED_OFF"
    if (project_dir / WORKFLOW_STAGES["QA_PASSED"]["file"]).exists():
        return "QA_PASSED"
    if (project_dir / WORKFLOW_STAGES["COMPLETED"]["file"]).exists():
        return "COMPLETED"
    return "IN_PROGRESS"


def get_project_summary(project_dir: Path) -> str:
    """The core logic for displaying the project summary, returned as a string."""
    project_dir = project_dir.resolve()
    summary_lines = [f"--- Project Summary: {project_dir} ---"]

    # 1. Workflow Stage
    stage_key = get_workflow_stage(project_dir)
    stage_name = WORKFLOW_STAGES[stage_key]['name']
    summary_lines.append(f"  {'Workflow Stage':<20}: {stage_name}")

    # 2. Key Artifacts
    artifacts = {
        "Feature Plan": "feature_list.json",
        "QA Summary": "qa_summary.txt",
        "Reviewer Report": "reviewer_report.txt",
    }
    found_artifacts = []
    for name, path in artifacts.items():
        if (project_dir / path).exists():
            found_artifacts.append(name)

    if found_artifacts:
        summary_lines.append(f"  {'Key Artifacts':<20}: {', '.join(found_artifacts)}")
    else:
        summary_lines.append(f"  {'Key Artifacts':<20}: None")

    # 3. Git Status
    try:
        git_path = shutil.which("git")
        if not git_path or not (project_dir / ".git").is_dir():
            summary_lines.append(f"  {'Git Status':<20}: Not a git repository.")
        else:
            result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain", "-b"],
                capture_output=True, text=True, check=True
            )
            lines = result.stdout.strip().split('\n')
            branch_line = lines[0]
            status_lines = lines[1:]
            branch_name = branch_line.split(' ')[1].split('...')[0]
            status = "Clean"
            if status_lines:
                status = f"{len(status_lines)} uncommitted change(s)"
            summary_lines.append(f"  {'Git Branch':<20}: {branch_name}")
            summary_lines.append(f"  {'Git Status':<20}: {status}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        summary_lines.append(f"  {'Git Status':<20}: Error checking status ({e})")

    # 4. Last Activity
    history_file = project_dir / ".agent_history"
    if history_file.exists():
        try:
            with open(history_file, "r") as f:
                run_ids = [line.strip() for line in f if line.strip()]
            if run_ids:
                last_run_id = run_ids[-1]
                summary_lines.append(f"  {'Last Run ID':<20}: {last_run_id}")
            else:
                summary_lines.append(f"  {'Last Activity':<20}: No runs in history.")
        except IOError:
            summary_lines.append(f"  {'Last Activity':<20}: Error reading history file.")
    else:
        summary_lines.append(f"  {'Last Activity':<20}: No agent runs recorded.")

    return "\n".join(summary_lines)


def _run_enhanced_status_logic(project_dir: Path) -> str:
    """The core logic for the enhanced status command, returned as a string."""
    project_dir = project_dir.resolve()
    lines = [f"--- Project Status: {project_dir} ---"]

    # 1. Workflow Stage
    stage_key = get_workflow_stage(project_dir)
    stage_name = WORKFLOW_STAGES[stage_key]['name']
    lines.append(f"\n[ Workflow: {stage_name} ]")

    # 2. Feature Summary
    lines.append("\n[ Feature Summary ]")
    feature_file = project_dir / "feature_list.json"
    if feature_file.exists():
        try:
            with open(feature_file, 'r') as f:
                features = json.load(f)
            if isinstance(features, list) and features:
                lines.append(f"  Found {len(features)} features in feature_list.json:")
                for i, feature in enumerate(features[:3]): # Show top 3
                    lines.append(f"    - {feature}")
                if len(features) > 3:
                    lines.append("    ...")
            else:
                lines.append("  feature_list.json is empty or invalid.")
        except (json.JSONDecodeError, IOError):
            lines.append("  Could not parse feature_list.json.")
    else:
        lines.append("  No feature_list.json found.")

    # 3. Recent Activity Timeline
    lines.append("\n[ Recent Activity ]")
    history_file = project_dir / ".agent_history"
    if history_file.exists():
        try:
            with open(history_file, "r") as f:
                run_ids = [line.strip() for line in f if line.strip()]
            if run_ids:
                # Display last 5 runs
                for run_id in reversed(run_ids[-5:]):
                    # Extract timestamp from run_id
                    try:
                        dt_part = run_id.split('-')[-1]
                        # Handling different timestamp formats that might exist
                        if len(dt_part) == 14: # YYYYMMDDHHMMSS
                            timestamp = datetime.strptime(dt_part, "%Y%m%d%H%M%S")
                            lines.append(f"  - {timestamp.strftime('%Y-%m-%d %H:%M:%S')} : Agent Run ({run_id})")
                        elif len(dt_part) > 14: # ISO format with microseconds
                             timestamp = datetime.fromisoformat(dt_part.replace('Z', '+00:00'))
                             lines.append(f"  - {timestamp.strftime('%Y-%m-%d %H:%M:%S')} : Agent Run ({run_id})")
                        else:
                             lines.append(f"  - Agent Run ({run_id})")
                    except (ValueError, IndexError):
                        lines.append(f"  - Agent Run ({run_id})")
            else:
                lines.append("  No agent runs recorded in history.")
        except IOError:
            lines.append("  Could not read agent history file.")
    else:
        lines.append("  No agent activity recorded.")

    # 4. Git Status / Recent File Changes
    lines.append("\n[ Recent File Changes ]")
    try:
        git_path = shutil.which("git")
        if not git_path or not (project_dir / ".git").is_dir():
            lines.append("  Not a git repository.")
        else:
            result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            changes = result.stdout.strip()
            if not changes:
                lines.append("  ✅ No uncommitted changes.")
            else:
                for line in changes.split('\n'):
                    lines.append(f"  {line}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        lines.append("  Could not retrieve git status.")

    # 5. Latest Run Metrics
    lines.append("\n[ Latest Run Metrics ]")
    metrics_file = project_dir / "final_metrics.txt"
    if metrics_file.exists():
        metrics = _parse_metrics(metrics_file)
        if metrics:
            time_val = metrics.get("Total Execution Time (s)")
            time_str = _format_duration(time_val) if isinstance(time_val, (int, float)) else "N/A"

            lines.append(f"  - Run Time:     {time_str}")
            lines.append(f"  - Iterations:   {metrics.get('Total Iterations', 'N/A')}")
            lines.append(f"  - Errors:       {metrics.get('Total Errors', 'N/A')}")
            lines.append(f"  - Tokens Used:  {metrics.get('LLM Tokens Used', 'N/A')}")
        else:
            lines.append("  Could not parse metrics file.")
    else:
        lines.append("  No metrics file found for the last run.")

    # 6. Actionable Suggestions
    lines.append("\n[ Next Steps ]")
    suggestions = get_suggestions(project_dir)
    if suggestions:
        for suggestion in suggestions[:3]: # Show top 3
            lines.append(f"  - {suggestion['reason']}")
            lines.append(f"    👉 `{suggestion['command']}`")
    else:
        lines.append("  ✅ Project is in a clean state. No specific actions to suggest.")

    return "\n".join(lines)


def _parse_metrics(metrics_file: Path) -> dict:
    """Parses a final_metrics.txt file into a dictionary (handles key:value and Prometheus formats)."""
    metrics = {}
    try:
        with open(metrics_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Legacy Format: Key: Value
                if ':' in line and '{' not in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    try:
                        if '.' in value:
                            metrics[key] = float(value)
                        else:
                            metrics[key] = int(value)
                    except ValueError:
                        metrics[key] = value

                # Prometheus Format: name{labels} value
                else:
                    # Regex to match: metric_name{label="value",...} 123.45
                    match = re.match(r'^(\w+)\{(.*)\}\s+(.+)$', line)
                    if match:
                        name, labels_str, value_str = match.groups()

                        # Parse value
                        try:
                            if '.' in value_str or 'e+' in value_str:
                                value = float(value_str)
                            else:
                                value = int(value_str)
                        except ValueError:
                            value = value_str

                        # Parse labels
                        labels = {}
                        for pair in labels_str.split(','):
                            if '=' in pair:
                                lk, lv = pair.split('=', 1)
                                labels[lk.strip()] = lv.strip('"')

                        # Map to friendly keys and aggregate where necessary
                        if name == "llm_tokens_total":
                            current_total = metrics.get("LLM Tokens Used", 0)
                            if isinstance(current_total, (int, float)) and isinstance(value, (int, float)):
                                metrics["LLM Tokens Used"] = current_total + value

                            # Keep raw breakdown for cost calculation (store in a special key or separate dict?)
                            # For simplicity, we just store it in the metrics dict with a unique key
                            type_label = labels.get("type", "unknown")
                            model_label = labels.get("model", "unknown")
                            breakdown_key = f"llm_tokens_total__{model_label}__{type_label}"
                            metrics[breakdown_key] = value

                            # Extract model if available
                            if "model" in labels:
                                metrics["Model"] = labels["model"]

                        elif name == "agent_errors_total":
                            current_errors = metrics.get("Total Errors", 0)
                            if isinstance(current_errors, (int, float)) and isinstance(value, (int, float)):
                                metrics["Total Errors"] = current_errors + value

                        elif name == "agent_iterations_total":
                            # Assuming this is a counter, so the latest value is the total
                            metrics["Total Iterations"] = value

                        elif name == "agent_uptime_seconds":
                             metrics["Total Execution Time (s)"] = value

                        elif name == "iteration_duration_seconds":
                             # This is likely a gauge for the last iteration duration
                             pass

                        # Also extract Agent Type and Run ID (agent_id)
                        if "agent_type" in labels:
                            metrics["Agent Type"] = labels["agent_type"]

                        if "agent_id" in labels:
                            metrics["Run ID"] = labels["agent_id"]

    except (IOError, FileNotFoundError):
        return {}
    return metrics


def _format_duration(seconds: float) -> str:
    """Formats seconds into a human-readable string (m s)."""
    seconds = float(seconds)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {seconds:.2f}s"


def _has_uncommitted_changes(project_dir: Path) -> bool:
    """Checks if there are uncommitted changes in the Git repository."""
    try:
        git_path = shutil.which("git")
        if not git_path or not (project_dir / ".git").is_dir():
            return False
        result = subprocess.run(
            [git_path, "-C", str(project_dir), "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        return bool(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_suggestions(project_dir: Path, limit: int = None) -> list[dict]:
    """
    Analyzes the project state and returns a list of suggested next commands.
    """
    suggestions = []
    stage = get_workflow_stage(project_dir)
    has_changes = _has_uncommitted_changes(project_dir)

    def add_suggestion(command, reason):
        if limit is not None and len(suggestions) >= limit:
            return False
        suggestions.append({"command": command, "reason": reason})
        return True

    # 1. Git-based suggestions
    if has_changes:
        if not add_suggestion("main.py diff-summary", "You have uncommitted changes. This command will show a summary of what has been modified."): return suggestions
        if not add_suggestion("main.py revert --interactive", "If the uncommitted changes are unwanted, you can use this command to interactively discard them."): return suggestions

    # 2. Workflow-based suggestions
    if stage == "COMPLETED":
        if not add_suggestion("main.py workflow advance", "The agent has completed its work. Advance the workflow to the 'QA Passed' stage if you have verified the results."): return suggestions
    elif stage == "QA_PASSED":
        if not add_suggestion("main.py workflow advance", "The project has passed QA. Advance to 'Signed Off' to finalize the project."): return suggestions
    elif stage == "SIGNED_OFF":
        if not add_suggestion("main.py clean --archive", "The project is complete. Archive the agent-generated artifacts to keep the directory clean."): return suggestions

    # 3. Artifact-based suggestions
    trash_dir = project_dir / ".agent_trash"
    if trash_dir.exists() and any(trash_dir.iterdir()):
        if not add_suggestion("main.py artifacts trash list", "You have items in the trash. Use this command to see what's there."): return suggestions
        if not add_suggestion("main.py artifacts trash restore", "If you need to recover deleted artifacts, you can restore them from the trash."): return suggestions

    # 4. General "what happened" suggestions
    if (project_dir / ".agent_run_id").exists():
        if not add_suggestion("main.py logs", "To see the logs from the last agent run."): return suggestions

    return suggestions


def get_latest_log_file() -> Path | None:
    """Finds the most recent agent log file."""
    # This assumes the script is run from the repo root, so paths are relative to `main.py`
    repo_root = Path(__file__).parent.parent
    logs_dir = repo_root / "agents/logs"

    if not logs_dir.exists():
        return None

    try:
        all_logs = sorted(logs_dir.glob('*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
        if all_logs:
            return all_logs[0]
    except OSError:
        return None
    return None


def get_all_log_files() -> list[Path]:
    """Returns a list of all log files sorted by modification time (newest first)."""
    # This assumes the script is run from the repo root, so paths are relative to `main.py`
    repo_root = Path(__file__).parent.parent
    logs_dir = repo_root / "agents/logs"

    if not logs_dir.exists():
        return []

    try:
        return sorted(logs_dir.glob('*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return []


def _find_metrics_file(run_id: str, project_dir: Path) -> Path | None:
    """Finds the final_metrics.txt file for a given run_id."""
    # 1. Check the main project directory
    metrics_file = project_dir / "final_metrics.txt"
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                content = f.read()
            if f"Run ID: {run_id}" in content:
                return metrics_file
        except IOError:
            pass

    # 2. Check archives and trash directories
    for base_dir_name in [".agent_archives", ".agent_trash"]:
        base_dir = project_dir / base_dir_name
        if base_dir.is_dir():
            for archive_dir in base_dir.iterdir():
                if archive_dir.is_dir():
                    metrics_file = archive_dir / "final_metrics.txt"
                    if metrics_file.exists():
                        try:
                            with open(metrics_file, 'r') as f:
                                content = f.read()
                            if f"Run ID: {run_id}" in content:
                                return metrics_file
                        except IOError:
                            continue
    return None


def _run_report_logic(run_id: str, output_path: Optional[Path], project_dir: Path, repo_root_for_test: Optional[Path] = None) -> bool:
    """The core logic for generating a run report."""
    project_dir = project_dir.resolve()
    repo_root = repo_root_for_test or Path(__file__).parent.parent
    log_file = repo_root / f"agents/logs/{run_id}.log"
    metrics_file = _find_metrics_file(run_id, project_dir)

    # --- Data Gathering ---
    if not log_file.exists():
        print(f"❌ Error: Log file not found for Run ID: {run_id}", file=sys.stderr)
        return False

    metrics = _parse_metrics(metrics_file) if metrics_file else {}
    log_content = log_file.read_text(encoding='utf-8', errors='ignore')
    log_lines = log_content.splitlines()

    # --- Report Generation ---
    report = [f"# Agent Run Report: {run_id}\n"]

    # 1. Summary Table
    report.append("## 📊 Summary\n")
    summary_table = [
        "| Metric | Value |",
        "|---|---|"
    ]
    timestamp = metrics.get("Timestamp", log_lines[0].split(" - ")[0] if log_lines else "N/A")
    summary_table.append(f"| **Run ID** | `{run_id}` |")
    summary_table.append(f"| **Timestamp** | {timestamp} |")
    summary_table.append(f"| **Agent** | {metrics.get('Agent Type', 'N/A')} |")
    summary_table.append(f"| **Model** | {metrics.get('Model', 'N/A')} |")
    time_val = metrics.get("Total Execution Time (s)")
    time_str = _format_duration(time_val) if isinstance(time_val, (int, float)) else "N/A"
    summary_table.append(f"| **Total Time** | {time_str} |")
    summary_table.append(f"| **Total Iterations** | {metrics.get('Total Iterations', 'N/A')} |")
    summary_table.append(f"| **Total Errors** | {metrics.get('Total Errors', 'N/A')} |")
    summary_table.append(f"| **Tokens Used** | {metrics.get('LLM Tokens Used', 'N/A')} |")
    report.extend(summary_table)
    report.append("\n")

    # 2. Code Changes (Git Commit)
    report.append("## 💻 Code Changes\n")
    git_path = shutil.which("git")
    commit_hash = None
    for line in log_lines:
        if "Git commit:" in line:
            commit_hash = line.split("Git commit:")[1].strip()
            break

    if commit_hash and git_path and (project_dir / ".git").is_dir():
        report.append(f"Found commit associated with this run: `{commit_hash}`\n")
        try:
            cmd = [git_path, "-C", str(project_dir), "show", "--stat", commit_hash]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            report.append("```diff")
            report.append(result.stdout.strip())
            report.append("```\n")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            stderr = getattr(e, 'stderr', str(e))
            report.append(f"Could not retrieve commit details: {stderr}\n")
    else:
        report.append("No Git commit was explicitly linked in the logs for this run.\n")

    # 3. Notable Log Events
    report.append("## 📝 Notable Log Events\n")
    notable_events = []
    for line in log_lines:
        if any(keyword in line for keyword in ["ERROR", "WARNING", "Manager", "Human-in-the-loop", "COMPLETED", "QA_PASSED", "PROJECT_SIGNED_OFF"]):
            notable_events.append(f"- `{line.strip()}`")

    if notable_events:
        report.extend(notable_events)
    else:
        report.append("No specific high-priority events found in the log.")
    report.append("\n")

    # --- Output ---
    final_report = "\n".join(report)
    if output_path:
        try:
            output_path.write_text(final_report, encoding='utf-8')
            print(f"✅ Report saved successfully to: {output_path}")
        except IOError as e:
            print(f"❌ Error writing report to file: {e}", file=sys.stderr)
            return False
    else:
        print(final_report)

    return True

def _run_tree_logic(project_dir: Path, depth: Optional[int], full: bool) -> str:
    """
    The core logic for generating a tree view of a directory.
    - project_dir: The root directory to start the tree from.
    - depth: How many levels of the tree to display. None for unlimited.
    - full: If False, respects .gitignore. If True, shows all files.
    """
    project_dir = project_dir.resolve()
    if not project_dir.is_dir():
        return f"Error: '{project_dir}' is not a valid directory."

    output_lines = [f"{project_dir.name}/"]
    git_path = shutil.which("git")
    is_git_repo = git_path and (project_dir / ".git").is_dir()

    def is_ignored(path: Path) -> bool:
        """Checks if a path is ignored by Git."""
        if full or not is_git_repo:
            return False
        try:
            # Use relative path from the project root for check-ignore
            relative_path = path.relative_to(project_dir)
            # The command returns 0 if the path is ignored, 1 if not.
            return subprocess.run(
                [git_path, "-C", str(project_dir), "check-ignore", "--quiet", str(relative_path)],
            ).returncode == 0
        except Exception:
            # If any error occurs (e.g., path is outside repo), treat as not ignored
            return False

    def generate_tree_recursive(directory: Path, prefix: str, current_depth: int):
        if depth is not None and current_depth >= depth:
            return

        try:
            # Sort entries, directories first, then by name
            entries = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            # Could be a permissions error
            return

        # Filter out ignored entries before determining pointers
        visible_entries = [e for e in entries if not is_ignored(e)]

        if not visible_entries:
            return

        # Use appropriate connectors for the last item in a directory
        pointers = ["├── "] * (len(visible_entries) - 1) + ["└── "]
        for pointer, path in zip(pointers, visible_entries):
            # Check if path is a directory for the suffix
            suffix = "/" if path.is_dir() else ""
            output_lines.append(f"{prefix}{pointer}{path.name}{suffix}")

            if path.is_dir():
                # Determine the prefix for the next level of recursion
                extension = "│   " if pointer == "├── " else "    "
                generate_tree_recursive(path, prefix + extension, current_depth + 1)

    generate_tree_recursive(project_dir, "", 0)
    return "\n".join(output_lines)

def _run_dashboard_logic(project_dir: Path) -> str:
    """The core logic for the dashboard command, returned as a string."""
    project_dir = project_dir.resolve()
    lines = [f"--- Project Dashboard: {project_dir.name} ---\n"]

    # --- 1. Workflow Status ---
    lines.append("[ Workflow ]")
    stage_key = get_workflow_stage(project_dir)
    stage_info = WORKFLOW_STAGES.get(stage_key, {})
    stage_name = stage_info.get("name", "Unknown")
    lines.append(f"  Status: {stage_name}")

    current_index = WORKFLOW_ORDER.index(stage_key)
    if stage_key != "SIGNED_OFF":
        next_stage_key = WORKFLOW_ORDER[current_index + 1]
        next_stage_name = WORKFLOW_STAGES[next_stage_key]["name"]
        lines.append(f"  Next: `main.py workflow advance` to move to '{next_stage_name}'.\n")
    else:
        lines.append("  Project is complete.\n")


    # --- 2. Git Status ---
    lines.append("[ Git ]")
    try:
        git_path = shutil.which("git")
        if not git_path or not (project_dir / ".git").is_dir():
            lines.append("  Not a git repository.\n")
        else:
            # Get branch
            branch_result = subprocess.run(
                [git_path, "-C", str(project_dir), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, check=True
            )
            branch_name = branch_result.stdout.strip()
            lines.append(f"  Branch: {branch_name}")

            # Get status
            status_result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            changes = status_result.stdout.strip()
            if not changes:
                lines.append("  Status: ✅ Clean\n")
            else:
                lines.append("  Status: ⚠️ Uncommitted changes\n")

    except (subprocess.CalledProcessError, FileNotFoundError):
        lines.append("  Could not retrieve git status.\n")


    # --- 3. Last Run Summary ---
    lines.append("[ Last Run ]")
    history_file = project_dir / ".agent_history"
    if history_file.exists():
        try:
            with open(history_file, "r") as f:
                run_ids = [line.strip() for line in f if line.strip()]
            if run_ids:
                last_run_id = run_ids[-1]
                lines.append(f"  Run ID: {last_run_id}")

                metrics_file = _find_metrics_file(last_run_id, project_dir)
                if metrics_file:
                    metrics = _parse_metrics(metrics_file)
                    time_val = metrics.get("Total Execution Time (s)")
                    time_str = _format_duration(time_val) if isinstance(time_val, (int, float)) else "N/A"
                    lines.append(f"  - Execution Time: {time_str}")
                    lines.append(f"  - Iterations:     {metrics.get('Total Iterations', 'N/A')}")
                    lines.append(f"  - Errors:         {metrics.get('Total Errors', 'N/A')}")
                else:
                    lines.append("  - No metrics file found for this run.")
            else:
                lines.append("  No runs in history.")
        except IOError:
            lines.append("  Could not read history file.")
    else:
        lines.append("  No agent runs recorded.")
    lines.append("")

    # --- 4. Suggested Commands ---
    lines.append("[ Suggested Commands ]")
    suggestions = get_suggestions(project_dir)
    if suggestions:
        for suggestion in suggestions[:3]:
            lines.append(f"  - {suggestion['reason']}")
            lines.append(f"    👉 `{suggestion['command']}`")
    else:
        lines.append("  ✅ Project is in a clean state.")

    return "\n".join(lines)


import shlex

def _run_next_logic(project_dir: Path) -> bool:
    """
    The core logic for the 'next' command.
    Finds the most relevant suggestion and offers to execute it.
    """
    project_dir = project_dir.resolve()
    suggestions = get_suggestions(project_dir, limit=1)

    if not suggestions:
        print("✅ Project is in a clean state. No specific next action to suggest.")
        print("   Try running the agent with a spec file (`main.py --spec app_spec.txt`) to start a new task.")
        return True

    suggestion = suggestions[0]
    command_str = suggestion['command']
    reason = suggestion['reason']

    print("--- Suggested Next Step ---")
    print(f"Reason: {reason}")
    print(f"Command: `{command_str}`")

    try:
        confirm = input("\nDo you want to execute this command? [Y/n]: ").strip().lower()
        if confirm not in ['y', '']:
            print("Aborted.")
            return True # Returning True because the operation was not a failure.

    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        return True

    print(f"\n--- Executing: {command_str} ---")

    try:
        # We need to construct the command to run main.py from the current executable
        executable_path = sys.executable
        main_script_path = Path(__file__).parent.parent / "main.py"

        # Use shlex.split to handle arguments correctly
        command_parts = shlex.split(command_str)

        # The suggested command is like "main.py commit", so we replace "main.py"
        # with the full path to the script.
        if command_parts and "main.py" in command_parts[0]:
            actual_command = [str(executable_path), str(main_script_path)] + command_parts[1:]
        else:
             # This case is unlikely if suggestions are formatted correctly, but it's a safe fallback.
             print(f"Warning: Could not determine how to execute '{command_str}'.", file=sys.stderr)
             return False

        # Execute the command, streaming its output
        result = subprocess.run(actual_command, cwd=project_dir)

        if result.returncode == 0:
            print("\n--- Command finished successfully ---")
            return True
        else:
            print(f"\n--- Command finished with an error (exit code: {result.returncode}) ---", file=sys.stderr)
            return False

    except FileNotFoundError:
        print(f"❌ Error: Command not found. Is '{executable_path}' in your PATH?", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred while executing the command: {e}", file=sys.stderr)
        return False


def _run_blame_logic(project_dir: Path, filepath: Path) -> str:
    """
    The core logic for the blame command. Shows the agent Run ID or author for each line.
    """
    project_dir = project_dir.resolve()
    target_file = filepath.resolve()

    # --- Pre-flight Checks ---
    git_path = shutil.which("git")
    if not git_path or not (project_dir / ".git").is_dir():
        return "❌ Error: Not a git repository. Cannot run blame."

    if not target_file.exists():
        return f"❌ Error: File not found at '{target_file}'"

    try:
        relative_path = target_file.relative_to(project_dir)
    except ValueError:
        return f"❌ Error: The file '{target_file}' is not inside the project directory '{project_dir}'."

    # --- Execute git blame ---
    try:
        # Use --porcelain format for machine-readable output
        cmd = [git_path, "-C", str(project_dir), "blame", "--porcelain", str(relative_path)]
        blame_result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        lines = blame_result.stdout.strip().split('\n')
        if not lines:
            return "Could not get blame information for this file."

    except subprocess.CalledProcessError as e:
        return f"❌ Error running git blame: {e.stderr}"

    # --- Process blame output ---
    output = []
    commit_info_cache = {} # Cache for storing Run ID or author for a given commit hash

    # First pass: Parse porcelain output to gather commit data for each line
    line_blame_info = []
    i = 0
    while i < len(lines):
        # The first line of a group is the commit hash and line info
        commit_hash, orig_line, final_line, _ = lines[i].split(" ")

        # Subsequent lines are metadata until the line starting with '\t'
        j = i + 1
        while not lines[j].startswith('\t'):
            j += 1

        code_line = lines[j][1:] # The actual line of code
        line_blame_info.append({"hash": commit_hash, "code": code_line})
        i = j + 1

    # Second pass: Process unique commits to get Run IDs or author info
    unique_commits = set(info["hash"] for info in line_blame_info)
    for commit_hash in unique_commits:
        if commit_hash not in commit_info_cache:
            try:
                # Get the full commit message to search for the Run ID
                show_cmd = [git_path, "-C", str(project_dir), "show", "-s", "--format=%B", commit_hash]
                show_result = subprocess.run(show_cmd, capture_output=True, text=True, check=True)
                commit_message = show_result.stdout

                # Search for "Run ID:"
                run_id_found = None
                for line in commit_message.split('\n'):
                    if "Run ID:" in line:
                        run_id_found = line.split("Run ID:")[1].strip()
                        break

                if run_id_found:
                    commit_info_cache[commit_hash] = f"Run ID: {run_id_found}"
                else:
                    # Fallback to author name if no Run ID is found
                    author_cmd = [git_path, "-C", str(project_dir), "show", "-s", "--format=%an", commit_hash]
                    author_result = subprocess.run(author_cmd, capture_output=True, text=True, check=True)
                    commit_info_cache[commit_hash] = f"Author: {author_result.stdout.strip()}"
            except subprocess.CalledProcessError:
                commit_info_cache[commit_hash] = "Unknown"

    # --- Format the output ---
    max_info_len = 0
    if commit_info_cache:
        max_info_len = max(len(info) for info in commit_info_cache.values())

    for i, info in enumerate(line_blame_info):
        commit_hash = info["hash"]
        blame_info_str = commit_info_cache.get(commit_hash, "Unknown").ljust(max_info_len)
        line_num = str(i + 1).rjust(4)
        output.append(f"{commit_hash[:8]} ({blame_info_str}) {line_num}: {info['code']}")

    return "\n".join(output)


IGNORE_DIRS = {'.git', '.vscode', '__pycache__', 'node_modules'}


def _run_context_show_logic(project_dir: Path) -> str:
    """
    The core logic for showing the agent's context with file sizes.
    - project_dir: The root directory to analyze.
    """
    project_dir = project_dir.resolve()
    if not project_dir.is_dir():
        return f"Error: '{project_dir}' is not a valid directory."

    output_lines = [f"--- Agent Context Analysis: {project_dir.name}/ ---\n"]
    git_path = shutil.which("git")
    is_git_repo = git_path and (project_dir / ".git").is_dir()

    total_files = 0
    total_size = 0
    large_files = []
    LARGE_FILE_THRESHOLD = 1024 * 1024  # 1 MB

    def format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes / (1024 * 1024):.1f} MB"

    def is_git_ignored(path: Path) -> bool:
        """Checks if a path is ignored by Git."""
        if not is_git_repo:
            return False
        try:
            relative_path = path.relative_to(project_dir)
            # Use --quiet to suppress errors for untracked files, and check return code
            return subprocess.run(
                [git_path, "-C", str(project_dir), "check-ignore", "--quiet", str(relative_path)],
            ).returncode == 0
        except Exception:
            return False

    def generate_tree_recursive(directory: Path, prefix: str):
        nonlocal total_files, total_size
        try:
            # Filter out ignored directories before iterating
            entries = sorted([p for p in directory.iterdir() if p.name not in IGNORE_DIRS and not is_git_ignored(p)],
                             key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return

        if not entries:
            return

        pointers = ["├── "] * (len(entries) - 1) + ["└── "]
        for pointer, path in zip(pointers, entries):
            if path.is_dir():
                output_lines.append(f"{prefix}{pointer}{path.name}/")
                extension = "│   " if pointer == "├── " else "    "
                generate_tree_recursive(path, prefix + extension)
            else:
                try:
                    size = path.stat().st_size
                    total_files += 1
                    total_size += size
                    size_str = format_size(size).rjust(10)
                    warning_marker = "⚠️ " if size > LARGE_FILE_THRESHOLD else ""
                    if warning_marker:
                        large_files.append((path.relative_to(project_dir), size))

                    output_lines.append(f"{prefix}{pointer}{warning_marker}{path.name} ({size_str})")
                except OSError:
                    output_lines.append(f"{prefix}{pointer}{path.name} (Error reading size)")

    generate_tree_recursive(project_dir, "")

    # --- Summary Section ---
    output_lines.append("\n--- Context Summary ---")
    output_lines.append(f"  Total Files:      {total_files}")
    output_lines.append(f"  Total Size:       {format_size(total_size)}")
    if large_files:
        output_lines.append(f"\n  Large Files (> {format_size(LARGE_FILE_THRESHOLD)}):")
        for path, size in sorted(large_files, key=lambda x: x[1], reverse=True):
            output_lines.append(f"    - {path} ({format_size(size)})")

    return "\n".join(output_lines)


def _run_context_analyze_logic(project_dir: Path) -> str:
    """
    The core logic for analyzing the agent's context by file type.
    - project_dir: The root directory to analyze.
    """
    project_dir = project_dir.resolve()
    if not project_dir.is_dir():
        return f"Error: '{project_dir}' is not a valid directory."

    output_lines = [f"--- Agent Context Analysis by File Type: {project_dir.name}/ ---\n"]
    git_path = shutil.which("git")
    is_git_repo = git_path and (project_dir / ".git").is_dir()

    file_stats = {}
    total_files = 0
    total_size = 0

    def format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes / (1024 * 1024):.1f} MB"

    def is_git_ignored(path: Path) -> bool:
        if not is_git_repo:
            return False
        try:
            relative_path = path.relative_to(project_dir)
            return subprocess.run(
                [git_path, "-C", str(project_dir), "check-ignore", "--quiet", str(relative_path)],
            ).returncode == 0
        except Exception:
            return False

    for root, dirs, files in os.walk(project_dir, topdown=True):
        root_path = Path(root)

        # Prune directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not is_git_ignored(root_path / d)]

        for name in files:
            file_path = root_path / name
            if not is_git_ignored(file_path):
                try:
                    size = file_path.stat().st_size
                    ext = file_path.suffix if file_path.suffix else "(no extension)"

                    if ext not in file_stats:
                        file_stats[ext] = {"count": 0, "size": 0}

                    file_stats[ext]["count"] += 1
                    file_stats[ext]["size"] += size
                    total_files += 1
                    total_size += size
                except OSError:
                    continue

    if not file_stats:
        return "No files found in the project context."

    sorted_stats = sorted(file_stats.items(), key=lambda item: item[1]['size'], reverse=True)

    max_ext_len = max(len(ext) for ext in file_stats.keys()) if file_stats else 10
    max_count_len = max(len(str(stats['count'])) for stats in file_stats.values()) if file_stats else 5
    max_size_len = max(len(format_size(stats['size'])) for stats in file_stats.values()) if file_stats else 10

    header = f"{'Extension':<{max_ext_len}} | {'Count':>{max_count_len}} | {'Total Size':>{max_size_len}} | Percentage"
    output_lines.append(header)
    output_lines.append("-" * len(header))

    for ext, stats in sorted_stats:
        size_str = format_size(stats['size'])
        percentage = (stats['size'] / total_size * 100) if total_size > 0 else 0
        output_lines.append(
            f"{ext:<{max_ext_len}} | {stats['count']:>{max_count_len}} | {size_str:>{max_size_len}} | {percentage:6.2f}%"
        )

    output_lines.append("-" * len(header))
    output_lines.append(
        f"{'TOTAL':<{max_ext_len}} | {total_files:>{max_count_len}} | {format_size(total_size):>{max_size_len}} | 100.00%"
    )

    return "\n".join(output_lines)

def _run_history_graph_logic(project_dir: Path, metric: str = "tokens", limit: int = 10) -> str:
    """
    Generates an ASCII chart for historical metrics.

    Args:
        project_dir: Path to the project.
        metric: One of 'tokens', 'duration', 'errors', 'iterations'.
        limit: Number of recent runs to show.
    """
    history_file = project_dir / ".agent_history"
    if not history_file.exists():
        return "No agent history found."

    try:
        with open(history_file, "r") as f:
            run_ids = [line.strip() for line in f if line.strip()]
    except IOError:
        return "Error reading history file."

    if not run_ids:
        return "History is empty."

    # Limit to last N runs
    recent_runs = run_ids[-limit:]
    data = {}

    for run_id in recent_runs:
        metrics_file = _find_metrics_file(run_id, project_dir)
        val = 0.0
        if metrics_file:
            metrics = _parse_metrics(metrics_file)
            if metric == "tokens":
                val = float(metrics.get("LLM Tokens Used", 0))
            elif metric == "duration":
                val = float(metrics.get("Total Execution Time (s)", 0))
            elif metric == "errors":
                val = float(metrics.get("Total Errors", 0))
            elif metric == "iterations":
                val = float(metrics.get("Total Iterations", 0))

        # Use short run ID for label
        label = run_id[-6:]  # last 6 chars
        data[label] = val

    title_map = {
        "tokens": "LLM Tokens Used",
        "duration": "Execution Time (s)",
        "errors": "Total Errors",
        "iterations": "Total Iterations"
    }

    return draw_ascii_bar_chart(data, title=f"History: {title_map.get(metric, metric)}")
