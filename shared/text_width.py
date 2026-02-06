
# Approximate character widths for Verdana 11px
# Sourced from standard font metrics
CHAR_WIDTHS = {
    ' ': 4,
    '!': 4,
    '"': 5,
    '#': 7,
    '$': 7,
    '%': 11,
    '&': 9,
    "'": 3,
    '(': 5,
    ')': 5,
    '*': 5,
    '+': 7,
    ',': 4,
    '-': 5,
    '.': 4,
    '/': 4,
    '0': 7, '1': 7, '2': 7, '3': 7, '4': 7, '5': 7, '6': 7, '7': 7, '8': 7, '9': 7,
    ':': 4,
    ';': 4,
    '<': 7,
    '=': 7,
    '>': 7,
    '?': 7,
    '@': 12,
    'A': 8, 'B': 8, 'C': 8, 'D': 9, 'E': 7, 'F': 7, 'G': 9, 'H': 9, 'I': 4, 'J': 6, 'K': 8, 'L': 7, 'M': 10,
    'N': 9, 'O': 9, 'P': 7, 'Q': 9, 'R': 8, 'S': 8, 'T': 7, 'U': 9, 'V': 8, 'W': 11, 'X': 8, 'Y': 8, 'Z': 7,
    '[': 5,
    '\\': 4,
    ']': 5,
    '^': 7,
    '_': 6,
    '`': 4,
    'a': 7, 'b': 7, 'c': 6, 'd': 7, 'e': 7, 'f': 4, 'g': 7, 'h': 7, 'i': 3, 'j': 3, 'k': 6, 'l': 3, 'm': 10,
    'n': 7, 'o': 7, 'p': 7, 'q': 7, 'r': 5, 's': 6, 't': 4, 'u': 7, 'v': 6, 'w': 9, 'x': 6, 'y': 6, 'z': 5,
    '{': 5,
    '|': 3,
    '}': 5,
    '~': 7
}

DEFAULT_WIDTH = 7

def calculate_text_width(text: str) -> int:
    """
    Calculates the approximate pixel width of a string in Verdana 11px.
    """
    if not text:
        return 0

    width = 0
    for char in str(text):
        width += CHAR_WIDTHS.get(char, DEFAULT_WIDTH)

    return width
