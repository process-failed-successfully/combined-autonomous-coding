import shutil
from pathlib import Path
from shared.config_loader import get_config_path
from shared.cli_utils import (
    get_suggestions,
    _run_enhanced_status_logic
)


def run_onboard_logic(project_dir: Path) -> bool:
    """
    Runs the interactive onboarding wizard for new developers.
    """
    project_dir = project_dir.resolve()
    print(f"--- 🚀 Welcome to Project: {project_dir.name} ---")
    print("This wizard will help you get started with the codebase.\n")

    # 1. Configuration Check
    print("[1/5] Checking Configuration...")
    config_path = get_config_path()
    if not config_path or not config_path.exists():
        print("  ⚠️  Agent configuration file not found.")
        print("  👉 Action: Run `main.py configure` to set up API keys and preferences.")
    else:
        print(f"  ✅ Configuration found at: {config_path}")

    # 2. Environment Check (Simplified Doctor)
    print("\n[2/5] Checking Environment...")
    git_path = shutil.which("git")
    if git_path:
        print("  ✅ Git installed.")
    else:
        print("  ❌ Git not found. Please install Git.")

    # Check for python/node/go
    if (project_dir / "requirements.txt").exists() or (project_dir / "pyproject.toml").exists():
        print("  ℹ️  Python project detected.")
    elif (project_dir / "package.json").exists():
        print("  ℹ️  Node.js project detected.")
    elif (project_dir / "go.mod").exists():
        print("  ℹ️  Go project detected.")
    else:
        print("  ℹ️  Project type not explicitly detected (no standard marker files found).")

    # 3. Project Status
    print("\n[3/5] Project Status Snapshot...")
    # Use existing status logic
    status_text = _run_enhanced_status_logic(project_dir)
    # Indent it slightly for visual hierarchy? Or just print it.
    # The status text has its own headers, so let's just print it.
    print(status_text)

    # 4. Suggestions / Next Steps
    print("\n[4/5] Recommended First Steps...")
    suggestions = get_suggestions(project_dir, limit=3)
    if suggestions:
        for i, suggestion in enumerate(suggestions):
            print(f"  {i+1}. {suggestion['reason']}")
            print(f"     Command: `{suggestion['command']}`")
    else:
        print("  ✅ You are all caught up! No immediate actions required.")

    # 5. Final Greeting
    print("\n[5/5] Ready to Code!")
    print("  Here are some useful commands to explore:")
    print("  - Explore code structure: `main.py map` or `main.py tree`")
    print("  - Ask a question:         `main.py ask \"how does authentication work?\"`")
    print("  - Run tests:              `main.py test`")
    print("  - Create a new feature:   `main.py feature`")
    print("\nHappy coding!")
    return True
