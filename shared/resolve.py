import sys
from pathlib import Path
from typing import Optional, List, Dict

from shared.todos import scan_todos
from shared.refactor import RefactorManager

async def run_resolve_logic(
    project_dir: Path,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    interactive: bool = True,
    yes: bool = False
) -> bool:
    """
    Scans for TODOs and interactively resolves one using the AI agent.
    """
    project_dir = project_dir.resolve()
    print(f"--- Scanning for TODOs in: {project_dir} ---")

    try:
        todos = scan_todos(project_dir)
    except Exception as e:
        print(f"❌ Error scanning for TODOs: {e}", file=sys.stderr)
        return False

    if not todos:
        print("✅ No TODOs found.")
        return True

    # Sort todos by file and line
    todos.sort(key=lambda x: (x['file'], x['line']))

    # Display list
    print("\nFound the following items:")
    for i, todo in enumerate(todos):
        # Truncate text if too long
        text = todo['text']
        if len(text) > 60:
            text = text[:57] + "..."
        print(f"[{i+1}] {todo['file']}:{todo['line']} ({todo['tag']}) - {text}")

    selected_todo = None
    if interactive:
        print("\nEnter the number of the item to resolve, or press Enter to cancel.")
        try:
            selection = input("> ").strip()
            if not selection:
                print("Aborted.")
                return True

            index = int(selection) - 1
            if 0 <= index < len(todos):
                selected_todo = todos[index]
            else:
                print("❌ Invalid selection.")
                return False
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
            return False
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return True
    else:
        print("Non-interactive mode requires specific selection logic (not implemented). Use --interactive.")
        return False

    if not selected_todo:
        return False

    print(f"\n--- Resolving TODO: {selected_todo['text']} ---")
    print(f"File: {selected_todo['file']}")
    print(f"Line: {selected_todo['line']}")

    # Construct Instruction
    instruction = (
        f"Implement the following task found on line {selected_todo['line']}: '{selected_todo['text']}'. "
        f"The tag used was {selected_todo['tag']}. "
        "IMPORTANT: You must implement the logic described AND remove the TODO/FIXME comment from the code."
    )

    manager = RefactorManager(project_dir)
    target_file = project_dir / selected_todo['file']

    try:
        result = await manager.refactor_file(
            target_file=target_file,
            instruction=instruction,
            agent_type=agent_type,
            model=model
        )
    except Exception as e:
        print(f"❌ Error during resolution: {e}", file=sys.stderr)
        return False

    if not result["changed"]:
        print("✅ Agent determined no changes were necessary (or failed to produce code).")
        return True

    print("\n--- Proposed Changes ---")
    print(result["diff"])

    if not yes:
        confirm = input("\nDo you want to apply these changes? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            return True

    manager.apply_changes(target_file, result["new_content"])
    print(f"\n✅ Successfully resolved TODO in {target_file.name}")
    return True
