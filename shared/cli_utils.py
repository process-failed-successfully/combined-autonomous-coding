import shutil
import subprocess
import json
from pathlib import Path
import time
from shared.workflow import WORKFLOW_STAGES, _get_workflow_stage

def _run_summary_logic(project_dir):
    """The core logic for displaying the project summary."""
    project_dir = project_dir.resolve()
    summary = f"--- Project Summary: {project_dir} ---\n"

    # 1. Workflow Stage
    stage_key = _get_workflow_stage(project_dir)
    stage_name = WORKFLOW_STAGES[stage_key]['name']
    summary += f"  {'Workflow Stage':<20}: {stage_name}\n"

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
        summary += f"  {'Key Artifacts':<20}: {', '.join(found_artifacts)}\n"
    else:
        summary += f"  {'Key Artifacts':<20}: None\n"

    # 3. Git Status
    try:
        git_path = shutil.which("git")
        if not git_path or not (project_dir / ".git").is_dir():
            summary += f"  {'Git Status':<20}: Not a git repository.\n"
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
            summary += f"  {'Git Branch':<20}: {branch_name}\n"
            summary += f"  {'Git Status':<20}: {status}\n"
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        summary += f"  {'Git Status':<20}: Error checking status ({e})\n"

    # 4. Last Activity
    history_file = project_dir / ".agent_history"
    if history_file.exists():
        try:
            with open(history_file, "r") as f:
                run_ids = [line.strip() for line in f if line.strip()]
            if run_ids:
                last_run_id = run_ids[-1]
                summary += f"  {'Last Run ID':<20}: {last_run_id}\n"
            else:
                summary += f"  {'Last Activity':<20}: No runs in history.\n"
        except IOError:
            summary += f"  {'Last Activity':<20}: Error reading history file.\n"
    else:
        summary += f"  {'Last Activity':<20}: No agent runs recorded.\n"
    return summary

def _run_status_logic(project_dir):
    """The core logic for displaying the project status."""
    project_dir = project_dir.resolve()
    status = f"--- Project Status: {project_dir} ---\n"

    # 1. Workflow Stage
    status += "\n[ Workflow Stage ]\n"
    if (project_dir / "PROJECT_SIGNED_OFF").exists():
        status += "  ✅ Project Signed Off: The project is complete and verified.\n"
    elif (project_dir / "QA_PASSED").exists():
        status += "  🤔 QA Passed: Ready for final manager review and sign-off.\n"
    elif (project_dir / "COMPLETED").exists():
        status += "  ⏳ Completed: Agent has finished coding, pending QA verification.\n"
    else:
        status += "  🏃 In Progress: Agent is actively working or ready to start.\n"

    # 2. Feature Summary
    status += "\n[ Feature Summary ]\n"
    feature_file = project_dir / "feature_list.json"
    if feature_file.exists():
        try:
            with open(feature_file, 'r') as f:
                features = json.load(f)
            if isinstance(features, list) and features:
                status += f"  Found {len(features)} features in feature_list.json:\n"
                for i, feature in enumerate(features[:5]):
                    status += f"    - {feature}\n"
                if len(features) > 5:
                    status += "    ...\n"
            else:
                status += "  feature_list.json is empty or invalid.\n"
        except json.JSONDecodeError:
            status += "  Error: Could not parse feature_list.json.\n"
        except Exception as e:
            status += f"  An error occurred: {e}\n"
    else:
        status += "  No feature_list.json found.\n"

    # 3. Last Agent Run
    status += "\n[ Last Agent Run ]\n"
    run_id_file = project_dir / ".agent_run_id"
    if run_id_file.exists():
        run_id = run_id_file.read_text().strip()
        status += f"  Last Run ID: {run_id}\n"
        repo_root = Path(__file__).parent.parent
        log_file_path = repo_root / f"agents/logs/{run_id}.log"
        try:
            display_path = log_file_path.relative_to(project_dir.parent)
        except ValueError:
            display_path = log_file_path

        if log_file_path.exists():
            try:
                with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    lines = all_lines[-5:]
                if lines:
                    status += "  Log Snippet (last 5 lines):\n"
                    for line in lines:
                        status += f"    {line.strip()}\n"
                else:
                    status += "  Log file is empty.\n"
            except Exception as e:
                status += f"  Error reading log file: {e}\n"
        else:
            status += f"  Log file not found at: {display_path}\n"
    else:
        status += "  No .agent_run_id file found. Has the agent been run yet?\n"

    # 4. Git Status
    status += "\n[ Git Status ]\n"
    try:
        git_path = shutil.which("git")
        check_repo = subprocess.run(
            [git_path, "-C", str(project_dir), "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True
        )
        if check_repo.returncode == 0 and check_repo.stdout.strip() == "true":
            result = subprocess.run(
                [git_path, "-C", str(project_dir), "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            if result.stdout:
                status += "  Uncommitted changes detected:\n"
                for line in result.stdout.strip().split('\n'):
                    status += f"    {line}\n"
            else:
                status += "  ✅ Working directory is clean.\n"
        else:
            status += "  Directory is not a Git repository.\n"
    except FileNotFoundError:
        status += "  Git not found. Cannot determine repository status.\n"
    except subprocess.CalledProcessError as e:
        status += f"  Error checking git status: {e.stderr}\n"
    except Exception as e:
        status += f"  An unexpected error occurred while checking git status: {e}\n"
    return status
