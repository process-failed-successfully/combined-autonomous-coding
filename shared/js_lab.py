import argparse
import sys
import subprocess
import json
from pathlib import Path

class JsLabManager:
    def __init__(self):
        pass

    def run_code(self, code: str) -> dict:
        """Executes JavaScript code using Node.js and returns stdout, stderr, and success."""
        try:
            # We use node -e to evaluate the script
            # Ensure proper handling of timeouts to avoid hanging
            result = subprocess.run(
                ["node", "-e", code],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Execution timed out (10s limit).",
                "exit_code": -1
            }
        except Exception as e:
             return {
                "success": False,
                "stdout": "",
                "stderr": f"Error running Node.js: {e}",
                "exit_code": -1
            }

    def minify(self, code: str) -> dict:
        """A basic minifier that removes whitespace and comments, protecting strings."""
        import re

        # 1. Protect strings
        strings = []
        def repl_string(m):
            strings.append(m.group(0))
            return f"__STR_{len(strings)-1}__"

        minified = re.sub(r'("[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'|`[^`\\]*(?:\\.[^`\\]*)*`)', repl_string, code)

        # 2. Remove single line comments
        minified = re.sub(r'//.*', '', minified)

        # 3. Remove multi line comments
        minified = re.sub(r'/\*.*?\*/', '', minified, flags=re.DOTALL)

        # 4. Collapse spaces
        minified = re.sub(r'\s+', ' ', minified)

        # 5. Restore strings
        for i, s in reversed(list(enumerate(strings))):
            minified = minified.replace(f"__STR_{i}__", s)

        return {"success": True, "output": minified.strip()}

def run_js_lab_logic(args: argparse.Namespace) -> bool:
    try:
        manager = JsLabManager()

        if getattr(args, "action") == "run":
            code = ""
            if getattr(args, "file"):
                with open(args.file, 'r') as f:
                    code = f.read()
            elif getattr(args, "code"):
                code = args.code
            else:
                 if not sys.stdin.isatty():
                     code = sys.stdin.read()
                 else:
                     print("Error: --file, --code, or stdin required.", file=sys.stderr)
                     return False

            res = manager.run_code(code)

            if res["stdout"]:
                 print(res["stdout"], end="")
            if res["stderr"]:
                 print(res["stderr"], file=sys.stderr, end="")

            return res["success"]

        elif getattr(args, "action") == "minify":
            code = ""
            if getattr(args, "file"):
                with open(args.file, 'r') as f:
                    code = f.read()
            elif getattr(args, "code"):
                code = args.code
            else:
                if not sys.stdin.isatty():
                     code = sys.stdin.read()
                else:
                     print("Error: --file, --code, or stdin required.", file=sys.stderr)
                     return False

            res = manager.minify(code)
            if getattr(args, "output"):
                with open(args.output, 'w') as f:
                    f.write(res["output"])
                print(f"Minified JS written to {args.output}")
            else:
                print(res["output"])
            return True

        else:
            print("Invalid action or missing required arguments.", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error processing JS: {e}", file=sys.stderr)
        return False
