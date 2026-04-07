import re
import sys
import unicodedata

class SlugManager:
    """Manages string slugification."""

    def generate_slug(self, text: str) -> str:
        """
        Converts text into a URL-friendly slug.
        - Normalizes unicode (removes accents/diacritics).
        - Converts to lowercase.
        - Replaces spaces and non-alphanumeric characters with hyphens.
        - Removes leading/trailing hyphens.
        - Collapses multiple hyphens into a single one.
        """
        if not text:
            return ""

        # Normalize unicode: split combined characters and encode to ascii, ignoring errors
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

        # Convert to lowercase
        text = text.lower()

        # Replace non-alphanumeric characters with hyphens
        text = re.sub(r'[^a-z0-9]+', '-', text)

        # Strip leading/trailing hyphens and collapse multiple hyphens
        text = text.strip('-')

        return text

def run_slug_lab_logic(args):
    """CLI logic for Slug Lab."""

    if getattr(args, 'tui', False):
        from main import run_tui
        import asyncio

        # Prevent "Event loop is closed" by running TUI centrally
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                return
        except RuntimeError:
            pass

        run_tui(args, start_tab="tab-slug")
        return

    manager = SlugManager()

    if not args.text and not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        text = args.text

    if not text:
        print("Error: Input text required either via --text or stdin.", file=sys.stderr)
        sys.exit(1)

    result = manager.generate_slug(text)
    print(result)
    sys.exit(0)
