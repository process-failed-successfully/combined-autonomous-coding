"""
Lorem Ipsum Lab
Provides utilities to generate placeholder text.
"""
import random

LOREM_WORDS = [
    "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
    "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore",
    "magna", "aliqua", "enim", "ad", "minim", "veniam", "quis", "nostrud",
    "exercitation", "ullamco", "laboris", "nisi", "ut", "aliquip", "ex", "ea",
    "commodo", "consequat", "duis", "aute", "irure", "dolor", "in", "reprehenderit",
    "in", "voluptate", "velit", "esse", "cillum", "dolore", "eu", "fugiat", "nulla",
    "pariatur", "excepteur", "sint", "occaecat", "cupidatat", "non", "proident",
    "sunt", "in", "culpa", "qui", "officia", "deserunt", "mollit", "anim", "id", "est",
    "laborum"
]

class LoremLabManager:
    """Manager for generating lorem ipsum text."""

    def __init__(self):
        pass

    def generate_words(self, count: int, start_with_lorem: bool = True) -> str:
        """Generates a specific number of words."""
        if count <= 0:
            return ""

        words = []
        if start_with_lorem:
            words.extend(["Lorem", "ipsum", "dolor", "sit", "amet"])
            if count <= 5:
                return " ".join(words[:count])

        while len(words) < count:
            words.append(random.choice(LOREM_WORDS))

        return " ".join(words[:count]).capitalize()

    def generate_sentences(self, count: int, start_with_lorem: bool = True) -> str:
        """Generates a specific number of sentences."""
        if count <= 0:
            return ""

        sentences = []
        for i in range(count):
            # random length between 5 and 15 words
            length = random.randint(5, 15)
            sentence_words = []

            if i == 0 and start_with_lorem:
                sentence_words.extend(["lorem", "ipsum", "dolor", "sit", "amet"])
                while len(sentence_words) < length:
                    sentence_words.append(random.choice(LOREM_WORDS))
            else:
                for _ in range(length):
                    sentence_words.append(random.choice(LOREM_WORDS))

            sentence_words = sentence_words[:length]
            sentence = " ".join(sentence_words).capitalize() + "."
            sentences.append(sentence)

        return " ".join(sentences)

    def generate_paragraphs(self, count: int, start_with_lorem: bool = True) -> str:
        """Generates a specific number of paragraphs."""
        if count <= 0:
            return ""

        paragraphs = []
        for i in range(count):
            # random length between 3 and 7 sentences
            length = random.randint(3, 7)
            if i == 0 and start_with_lorem:
                paragraph = self.generate_sentences(length, start_with_lorem=True)
            else:
                paragraph = self.generate_sentences(length, start_with_lorem=False)
            paragraphs.append(paragraph)

        return "\n\n".join(paragraphs)

def run_lorem_lab_logic(args) -> bool:
    """CLI logic for the lorem lab."""
    import sys

    manager = LoremLabManager()

    count = getattr(args, "count", 1)
    text_type = getattr(args, "type", "paragraphs")
    no_start = getattr(args, "no_start", False)

    start_with_lorem = not no_start

    if text_type == "words":
        output = manager.generate_words(count, start_with_lorem)
    elif text_type == "sentences":
        output = manager.generate_sentences(count, start_with_lorem)
    elif text_type == "paragraphs":
        output = manager.generate_paragraphs(count, start_with_lorem)
    else:
        print(f"Error: Unknown type '{text_type}'", file=sys.stderr)
        return False

    print(output)
    return True
