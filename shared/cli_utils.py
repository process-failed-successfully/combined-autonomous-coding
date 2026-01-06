from pathlib import Path
import shutil
import subprocess

WORKFLOW_STAGES = {
    "IN_PROGRESS": {"name": "In Progress", "file": None},
    "COMPLETED": {"name": "Completed", "file": "COMPLETED"},
    "QA_PASSED": {"name": "QA Passed", "file": "QA_PASSED"},
    "SIGNED_OFF": {"name": "Signed Off", "file": "PROJECT_SIGNED_OFF"},
}

def _get_workflow_stage(project_dir: Path):
    """Determines the current workflow stage by checking for marker files."""
    if (project_dir / WORKFLOW_STAGES["SIGNED_OFF"]["file"]).exists():
        return "SIGNED_OFF"
    if (project_dir / WORKFLOW_STAGES["QA_PASSED"]["file"]).exists():
        return "QA_PASSED"
    if (project_dir / WORKFLOW_STAGES["COMPLETED"]["file"]).exists():
        return "COMPLETED"
    return "IN_PROGRESS"

def _run_summary_logic(project_dir):
    """The core logic for displaying the project summary."""
    project_dir = project_dir.resolve()
    output = [f"--- Project Summary: {project_dir} ---"]

    # 1. Workflow Stage
    stage_key = _get_workflow_stage(project_dir)
    stage_name = WORKFLOW_STAGES[stage_key]['name']
    output.append(f"  {'Workflow Stage':<20}: {stage_name}")

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
        output.append(f"  {'Key Artifacts':<20}: {', '.join(found_artifacts)}")
    else:
        output.append(f"  {'Key Artifacts':<20}: None")

    # 3. Git Status
    try:
        git_path = shutil.which("git")
        if not git_path or not (project_dir / ".git").is_dir():
            output.append(f"  {'Git Status':<20}: Not a git repository.")
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
            output.append(f"  {'Git Branch':<20}: {branch_name}")
            output.append(f"  {'Git Status':<20}: {status}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        output.append(f"  {'Git Status':<20}: Error checking status ({e})")

    # 4. Last Activity
    history_file = project_dir / ".agent_history"
    if history_file.exists():
        try:
            with open(history_file, "r") as f:
                run_ids = [line.strip() for line in f if line.strip()]
            if run_ids:
                last_run_id = run_ids[-1]
                output.append(f"  {'Last Run ID':<20}: {last_run_id}")
            else:
                output.append(f"  {'Last Activity':<20}: No runs in history.")
        except IOError:
            output.append(f"  {'Last Activity':<20}: Error reading history file.")
    else:
        output.append(f"  {'Last Activity':<20}: No agent runs recorded.")

    return "\n".join(output)
