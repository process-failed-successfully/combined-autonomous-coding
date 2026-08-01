import sys
import subprocess
from typing import Dict, Any
from pathlib import Path
import argparse


class SedLabManager:
    """Manages execution of SED scripts on text data."""

    def evaluate(self, text_data: str, script: str) -> Dict[str, Any]:
        """
        Evaluates a SED script against text data.

        Args:
            text_data: The text data to process.
            script: The SED script.

        Returns:
            A dictionary containing 'success' status, 'result' (stdout) or 'error' message.
        """
        if not text_data and not script:
            return {"success": False, "error": "Empty input and script"}

        if not script or not script.strip():
            return {"success": False, "error": "Empty SED script provided"}

        try:
            # We use sed from the system path
            process = subprocess.Popen(
                ['sed', script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=text_data)

            if process.returncode != 0:
                return {"success": False, "error": stderr.strip() or f"SED exited with code {process.returncode}"}

            return {
                "success": True,
                "result": stdout
            }

        except FileNotFoundError:
            return {"success": False, "error": "SED executable not found on the system."}
        except Exception as e:
            return {"success": False, "error": str(e)}


def run_sed_lab_logic(args: argparse.Namespace) -> bool:
    """Entry point for the SED Lab CLI."""
    manager = SedLabManager()

    text_data = ""

    # Read from file or stdin
    if args.input == "-":
        if sys.stdin.isatty():
            print("Error: No input provided on stdin.", file=sys.stderr)
            return False
        text_data = sys.stdin.read()
    else:
        path = Path(args.input)
        if not path.is_file():
            print(f"Error: File '{args.input}' not found.", file=sys.stderr)
            return False
        text_data = path.read_text(encoding='utf-8')

    result = manager.evaluate(text_data, args.script)

    if result["success"]:
        print(result["result"], end="")
        return True
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return False
