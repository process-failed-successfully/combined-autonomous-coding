import sys
import unicodedata
import re
import argparse

class SlugManager:
    @staticmethod
    def slugify(text: str) -> str:
        """
        Converts a string to a URL-friendly slug.
        Normalizes unicode, converts to lowercase, replaces non-alphanumeric chars with hyphens,
        and strips leading/trailing hyphens.
        """
        if not text:
            return ""

        # Normalize unicode (decompose characters like é to e + ´)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')

        # Convert to lowercase
        text = text.lower()

        # Replace non-alphanumeric characters with hyphens
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)

        # Strip leading and trailing hyphens
        return text.strip('-')

def run_slug_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for slug-lab."""
    if not getattr(args, 'text', None):
        print("Error: 'text' argument is required.", file=sys.stderr)
        return False

    manager = SlugManager()
    slug = manager.slugify(args.text)
    print(slug)
    return True
