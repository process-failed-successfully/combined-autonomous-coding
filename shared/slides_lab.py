from pathlib import Path
from typing import List, Dict, Any
import yaml


class SlideDeck:
    """
    Parses and manages a Markdown slide deck.
    """
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.slides: List[str] = []
        self.metadata: Dict[str, Any] = {}

    def load(self) -> None:
        """Loads the file and parses slides."""
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {self.filepath}")

        content = self.filepath.read_text(encoding="utf-8")

        # Check for frontmatter
        if content.startswith("---"):
            try:
                # Find the second ---
                end_fm = content.find("\n---", 3)
                if end_fm != -1:
                    fm_content = content[3:end_fm]
                    self.metadata = yaml.safe_load(fm_content) or {}
                    # The rest is the content
                    content = content[end_fm+4:].strip()
                else:
                    # Maybe it's just a separator, not frontmatter?
                    pass
            except Exception:
                # Fallback if yaml parsing fails
                pass

        # Split by ---
        # We need to be careful not to split frontmatter again if we didn't extract it correctly
        # But here we assume content is now stripped of frontmatter if it existed.

        # Basic split
        raw_slides = content.split("\n---\n")
        self.slides = [s.strip() for s in raw_slides if s.strip()]

        if not self.slides:
            # Maybe the file is just one slide without separators?
            if content.strip():
                self.slides = [content.strip()]
            else:
                self.slides = ["# Empty Presentation"]

    def get_slide(self, index: int) -> str:
        """Returns the content of the slide at index."""
        if 0 <= index < len(self.slides):
            return self.slides[index]
        return ""

    def __len__(self) -> int:
        return len(self.slides)
