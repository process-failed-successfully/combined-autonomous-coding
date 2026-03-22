import sys
import os
from pathlib import Path
from typing import List

def run_alias_lab_logic(args, known_commands: List[str]) -> bool:
    """
    Generates shell aliases for all known CLI commands.
    """
    shell = getattr(args, "shell", "bash").lower()
    prefix = getattr(args, "prefix", "")

    # We want to point to the absolute path of main.py
    main_py_path = Path(sys.argv[0]).resolve()

    if shell not in ["bash", "zsh", "fish"]:
        print(f"Error: Unsupported shell '{shell}'. Supported shells are: bash, zsh, fish.", file=sys.stderr)
        return False

    output = []

    # Sort commands for consistent output
    sorted_commands = sorted(set(known_commands))

    for cmd in sorted_commands:
        # Create the alias name by applying prefix
        alias_name = f"{prefix}{cmd}"

        if shell in ["bash", "zsh"]:
            output.append(f"alias {alias_name}='\"{main_py_path}\" {cmd}'")
        elif shell == "fish":
            output.append(f"alias {alias_name} '\"{main_py_path}\" {cmd}'")

    if output:
        print(f"# Aliases generated for {shell}")
        if prefix:
            print(f"# Prefix used: '{prefix}'")
        print("\n".join(output))
    else:
        print("No commands found to alias.", file=sys.stderr)

    return True
