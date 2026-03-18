class BrailleLabManager:
    # A simplified dictionary mapping ASCII to English Braille
    _TEXT_TO_BRAILLE = {
        'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑', 'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
        'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕', 'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
        'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽', 'z': '⠵',
        '1': '⠼⠁', '2': '⠼⠃', '3': '⠼⠉', '4': '⠼⠙', '5': '⠼⠑', '6': '⠼⠋', '7': '⠼⠛', '8': '⠼⠓', '9': '⠼⠊', '0': '⠼⠚',
        ',': '⠂', ';': '⠆', ':': '⠒', '.': '⠲', '!': '⠖', '(': '⠦', ')': '⠴', '?': '⠢', '"': '⠦', "'": '⠄', '-': '⠤',
        ' ': ' '
    }

    _BRAILLE_TO_TEXT = {v: k for k, v in _TEXT_TO_BRAILLE.items()}

    def encode(self, text: str) -> str:
        """Translates plain text into Braille Unicode characters."""
        if not text:
            return ""

        result = []
        for char in text.lower():
            if char in self._TEXT_TO_BRAILLE:
                result.append(self._TEXT_TO_BRAILLE[char])
            else:
                result.append(char)
        return "".join(result)

    def decode(self, braille_text: str) -> str:
        """Translates Braille Unicode characters back to plain text."""
        if not braille_text:
            return ""

        result = []
        i = 0
        while i < len(braille_text):
            # Check for numbers prefix
            if braille_text[i] == '⠼' and i + 1 < len(braille_text):
                combined = braille_text[i:i+2]
                if combined in self._BRAILLE_TO_TEXT:
                    result.append(self._BRAILLE_TO_TEXT[combined])
                    i += 2
                    continue

            char = braille_text[i]
            if char in self._BRAILLE_TO_TEXT:
                result.append(self._BRAILLE_TO_TEXT[char])
            else:
                result.append(char)
            i += 1

        return "".join(result)


def run_braille_lab_logic(args):
    """CLI handler for Braille Lab."""
    manager = BrailleLabManager()

    if args.action == "encode":
        print(manager.encode(args.text))
    elif args.action == "decode":
        print(manager.decode(args.text))
    elif args.action == "tui":
        from shared.tui import AgentTUI
        import asyncio
        app = AgentTUI(start_tab="tab-braille", project_dir=args.project_dir)
        try:
            loop = asyncio.get_running_loop()  # noqa: F841
            asyncio.ensure_future(app.run_async())
        except RuntimeError:
            app.run()
