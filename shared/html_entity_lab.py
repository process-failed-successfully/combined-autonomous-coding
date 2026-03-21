import sys
import html

class HtmlEntityLabManager:
    def encode(self, text: str) -> str:
        """Encodes characters to HTML entities."""
        return html.escape(text, quote=True)

    def decode(self, text: str) -> str:
        """Decodes HTML entities back to characters."""
        return html.unescape(text)

def run_html_entity_lab_logic(args):
    manager = HtmlEntityLabManager()

    if args.action == "tui":
        # Launch TUI
        from shared.tui import AgentTUI
        import asyncio
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-html-entity")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
        return

    text = args.text
    if not text and not sys.stdin.isatty():
        text = sys.stdin.read()

    if not text:
        print("Error: No text provided.", file=sys.stderr)
        sys.exit(1)

    try:
        if args.action == "encode":
            result = manager.encode(text)
            print(result)
        elif args.action == "decode":
            result = manager.decode(text)
            print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
