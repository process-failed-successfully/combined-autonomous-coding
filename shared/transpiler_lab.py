import io
import contextlib
import sys
from pathlib import Path
from typing import Optional
from shared.ask import run_ask_logic

class TranspilerManager:
    """
    Manages code transpilation using AI agents.
    """
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    async def transpile(self, content: str, source_lang: str, target_lang: str, agent_type: str = "gemini") -> str:
        """
        Transpiles code from source language to target language.
        """
        if not content.strip():
            return ""

        prompt = (
            f"You are an expert code transpiler. Convert the following {source_lang} code to {target_lang}.\n"
            f"Preserve the logic and functionality as closely as possible. "
            f"Use idiomatic {target_lang} code.\n"
            f"Output ONLY the converted code block (e.g. inside ```{target_lang} ... ```). "
            f"Do not include explanations unless absolutely necessary as comments in the code.\n\n"
            f"Source Code:\n```{source_lang}\n{content}\n```"
        )

        # We need to capture the output from run_ask_logic since it prints to stdout
        output_capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(output_capture):
                # We use verbose=False to keep logs minimal
                await run_ask_logic(
                    query=prompt,
                    project_dir=self.project_dir,
                    agent_type=agent_type,
                    verbose=False
                )

            response = output_capture.getvalue()

            # Basic cleanup: if response contains "--- Answer ---", extract it.
            # run_ask_logic prints:
            # \n--- Answer ---
            # {response}
            # --------------

            if "--- Answer ---" in response:
                parts = response.split("--- Answer ---")
                if len(parts) > 1:
                    response = parts[1]

            if "--------------" in response:
                response = response.split("--------------")[0]

            response = response.strip()

            # Strip markdown code blocks if present
            if response.startswith("```"):
                lines = response.splitlines()
                # Remove first line (```lang)
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove last line (```)
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                response = "\n".join(lines)

            return response.strip()

        except Exception as e:
            return f"Error during transpilation: {e}"

async def run_transpiler_lab_logic(args):
    """CLI Entry point for Transpiler Lab."""
    manager = TranspilerManager(args.project_dir)

    source_lang = args.source
    target_lang = args.target

    if args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching Transpiler Lab TUI...")
        app = AgentTUI(project_dir=args.project_dir, start_tab="tab-transpiler")
        app.run()
        sys.exit(0)

    # CLI Mode
    content = ""
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File {path} not found.", file=sys.stderr)
            sys.exit(1)
        content = path.read_text(encoding="utf-8", errors="replace")
    elif args.code:
        content = args.code
    else:
        # Try stdin
        if not sys.stdin.isatty():
            content = sys.stdin.read()

    if not content:
        print("Error: No input code provided. Use --file, --code, or pipe stdin.", file=sys.stderr)
        sys.exit(1)

    if not target_lang:
        print("Error: --target language required.", file=sys.stderr)
        sys.exit(1)

    # Default source to 'auto' if not provided? Prompt handles it reasonably well usually,
    # but explicit is better.
    if not source_lang:
        source_lang = "auto-detect"

    result = await manager.transpile(content, source_lang, target_lang, agent_type=args.agent or "gemini")
    print(result)
    sys.exit(0)
