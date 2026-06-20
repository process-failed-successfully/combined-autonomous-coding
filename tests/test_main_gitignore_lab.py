import subprocess
import sys
from pathlib import Path

def test_gitignore_lab_tui_flag():
    root_dir = Path(__file__).parent.parent
    main_script = root_dir / "main.py"

    # Testing that it passes parse
    result = subprocess.run(
        ["python3", "-c", f"import sys; sys.path.insert(0, '{root_dir}'); import main; parser = main.parse_args(['gitignore-lab', '--tui']); print(parser.command); print(parser.tui)"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "gitignore-lab" in result.stdout
    assert "True" in result.stdout

def test_gitignore_lab_missing_action():
    root_dir = Path(__file__).parent.parent
    main_script = root_dir / "main.py"

    result = subprocess.run(
        ["python3", str(main_script), "gitignore-lab"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert "Error: Action is required unless --tui is specified." in result.stderr
