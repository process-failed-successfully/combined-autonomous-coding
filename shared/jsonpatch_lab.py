import sys
import json
import jsonpatch
from pathlib import Path


class JsonPatchLabManager:
    def apply_patch(self, target_data, patch_data):
        """
        Applies a JSON Patch to target data.
        Returns the patched data as a JSON string, or dict if you pass dict.
        We'll accept either string or dict and return dict.
        """
        if isinstance(target_data, str):
            target_data = json.loads(target_data)

        if isinstance(patch_data, str):
            patch_data = json.loads(patch_data)

        try:
            patch = jsonpatch.JsonPatch(patch_data)
            result = patch.apply(target_data)
            return result
        except jsonpatch.JsonPatchException as e:
            raise ValueError(f"Patch error: {e}")
        except Exception as e:
            raise ValueError(f"Error applying patch: {e}")

    def diff(self, source_data, target_data):
        """
        Generates a JSON Patch to transform source_data into target_data.
        """
        if isinstance(source_data, str):
            source_data = json.loads(source_data)

        if isinstance(target_data, str):
            target_data = json.loads(target_data)

        try:
            patch = jsonpatch.make_patch(source_data, target_data)
            return patch.patch
        except Exception as e:
            raise ValueError(f"Error generating patch: {e}")

def run_jsonpatch_lab_logic(args):
    """CLI Entry point for JsonPatch Lab."""

    action = getattr(args, "jsonpatch_action", None)

    # Fallback to older args structure if tests use it
    if not action:
        action = getattr(args, "action", None)

    if action == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        import asyncio
        print("Launching JSONPatch Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-jsonpatch")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
            sys.exit(0)
        return

    manager = JsonPatchLabManager()

    if not action:
        # If no subcommand is specified, show help and exit
        import argparse
        print("Error: No command specified for jsonpatch-lab (apply, diff, tui).", file=sys.stderr)
        sys.exit(1)

    if action == "diff":
        if not getattr(args, "source", None):
            print("Error: --source is required.", file=sys.stderr)
            sys.exit(1)
        if not getattr(args, "target", None):
            print("Error: --target is required.", file=sys.stderr)
            sys.exit(1)

        # Read source
        source_path = Path(args.source)
        if source_path.exists() and source_path.is_file():
            try:
                source_content = source_path.read_text(encoding='utf-8')
            except IOError as e:
                print(f"Error reading source file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            source_content = args.source

        # Read target
        target_path = Path(args.target)
        if target_path.exists() and target_path.is_file():
            try:
                target_content = target_path.read_text(encoding='utf-8')
            except IOError as e:
                print(f"Error reading target file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            target_content = args.target

        try:
            result = manager.diff(source_content, target_content)
            print(json.dumps(result, indent=2))
            sys.exit(0)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        # Default action is apply
        if not getattr(args, "target", None):
            print("Error: --target is required.", file=sys.stderr)
            sys.exit(1)

        if not getattr(args, "patch", None):
            print("Error: --patch is required.", file=sys.stderr)
            sys.exit(1)

        # Read target
        target_path = Path(args.target)
        if target_path.exists() and target_path.is_file():
            try:
                target_content = target_path.read_text(encoding='utf-8')
            except IOError as e:
                print(f"Error reading target file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            target_content = args.target

        # Read patch
        if args.patch == "-":
            patch_content = sys.stdin.read()
        else:
            patch_path = Path(args.patch)
            if patch_path.exists() and patch_path.is_file():
                try:
                    patch_content = patch_path.read_text(encoding='utf-8')
                except IOError as e:
                    print(f"Error reading patch file: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                patch_content = args.patch

        try:
            result = manager.apply_patch(target_content, patch_content)
            print(json.dumps(result, indent=2))
            sys.exit(0)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}", file=sys.stderr)
            sys.exit(1)
