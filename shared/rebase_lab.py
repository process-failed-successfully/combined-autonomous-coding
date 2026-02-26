import sys
import os
import subprocess
from pathlib import Path

def run_rebase_lab_logic(args):
    """
    Runs the Interactive Git Rebase Lab.

    Two modes:
    1. Launcher: Sets GIT_SEQUENCE_EDITOR and runs 'git rebase -i'.
    2. Editor: Runs the TUI to edit the rebase todo file (invoked by git).
    """

    # Editor Mode
    if args.editor:
        from shared.tui_rebase import RebaseTUI

        file_path = Path(args.editor)
        app = RebaseTUI(file_path)
        # app.run() returns None usually, but we set exit code in the app actions
        # Textual apps exit with strict return codes if run via cli,
        # but here we are embedding.
        # We need to capture the result.
        # RebaseTUI.action_save_and_exit calls self.exit(result=0)
        # RebaseTUI.action_quit_app calls self.exit(result=1)

        ret = app.run()

        # If ret is None (default exit), we assume 0 or 1?
        # Textual default exit is usually cleanly.
        # But we want to signal success/failure.
        # If ret is an integer, we use it.

        if isinstance(ret, int):
            sys.exit(ret)
        else:
            sys.exit(0)

    # Launcher Mode
    else:
        target = args.target

        # Construct the editor command
        # We need to point back to the same main.py script
        # sys.executable is python3
        # sys.argv[0] is main.py path

        main_script = Path(sys.argv[0]).resolve()

        # We need to ensure we pass 'rebase-lab --editor'
        # Git appends the filename to the command.
        # So command should be "python3 /path/to/main.py rebase-lab --editor"
        # Git runs: $GIT_SEQUENCE_EDITOR <file>
        # Result: python3 /path/to/main.py rebase-lab --editor <file>

        # Note: argparse needs to handle the filename as 'editor' argument?
        # No, in main.py, we will define --editor as taking a value?
        # Or we can use a positional arg if we want.
        # Git passes the file path as the last argument.
        # So "python3 main.py rebase-lab --editor" results in args.editor being the file path IF --editor takes an arg.
        # Yes, we will define --editor as taking a string argument.

        editor_cmd = f"{sys.executable} {main_script} rebase-lab --editor"

        env = os.environ.copy()
        env["GIT_SEQUENCE_EDITOR"] = editor_cmd

        print(f"Starting Interactive Rebase on {target}...")
        print("Launching TUI editor...")

        try:
            subprocess.run(["git", "rebase", "-i", target], env=env, check=True)
            print("\n✅ Rebase completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Rebase failed or aborted (Exit code {e.returncode}).")
            sys.exit(e.returncode)
