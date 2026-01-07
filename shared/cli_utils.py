from pathlib import Path
import shutil
import subprocess
import json
from datetime import datetime

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

    # 5. Actionable Suggestions
    lines.append("\n[ Next Steps ]")
    suggestions = get_suggestions(project_dir)
    if suggestions:
        for suggestion in suggestions[:3]: # Show top 3
            lines.append(f"  - {suggestion['reason']}")
            lines.append(f"    👉 `{suggestion['command']}`")
    else:
        lines.append("  ✅ Project is in a clean state. No specific actions to suggest.")

    return "\n".join(lines)


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


def get_suggestions(project_dir: Path) -> list[dict]:
    """
    Analyzes the project state and returns a list of suggested next commands.
    """
    suggestions = []
    stage = get_workflow_stage(project_dir)
    has_changes = _has_uncommitted_changes(project_dir)

    # 1. Git-based suggestions
    if has_changes:
        suggestions.append({
            "command": "main.py diff-summary",
            "reason": "You have uncommitted changes. This command will show a summary of what has been modified."
        })
        suggestions.append({
            "command": "main.py revert --interactive",
            "reason": "If the uncommitted changes are unwanted, you can use this command to interactively discard them."
        })

    # 2. Workflow-based suggestions
    if stage == "COMPLETED":
        suggestions.append({
            "command": "main.py workflow advance",
            "reason": "The agent has completed its work. Advance the workflow to the 'QA Passed' stage if you have verified the results."
        })
    elif stage == "QA_PASSED":
        suggestions.append({
            "command": "main.py workflow advance",
            "reason": "The project has passed QA. Advance to 'Signed Off' to finalize the project."
        })
    elif stage == "SIGNED_OFF":
        suggestions.append({
            "command": "main.py clean --archive",
            "reason": "The project is complete. Archive the agent-generated artifacts to keep the directory clean."
        })

    # 3. Artifact-based suggestions
    trash_dir = project_dir / ".agent_trash"
    if trash_dir.exists() and any(trash_dir.iterdir()):
        suggestions.append({
            "command": "main.py artifacts trash list",
            "reason": "You have items in the trash. Use this command to see what's there."
        })
        suggestions.append({
            "command": "main.py artifacts trash restore",
            "reason": "If you need to recover deleted artifacts, you can restore them from the trash."
        })

    # 4. General "what happened" suggestions
    if (project_dir / ".agent_run_id").exists():
        suggestions.append({
            "command": "main.py logs",
            "reason": "To see the logs from the last agent run."
        })

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
