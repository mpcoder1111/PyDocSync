"""Sample representative module from Janome (Apache-2.0).

Source: mocobeta/janome (tokenizer.py extract)
"""

from typing import Iterator


class Token:
    """Morphological token representation."""

    def __init__(self, surface: str, pos: str, base_form: str, reading: str = "*") -> None:
        """Initialize token.

        Args:
            surface: Surface string form.
            pos: Part of speech tag.
            base_form: Base dictionary form.
            reading: Phonetic reading or pronunciation (default '*').
        """
        self.surface = surface
        self.pos = pos
        self.base_form = base_form
        self.reading = reading

    def is_punct(self) -> bool:
        """Check if token is punctuation."""
        return self.pos.startswith("記号") or self.pos.startswith("Punctuation")

    def format_node(self, sep: str = "\t") -> str:
        """Format token as tab-separated surface and features."""
        return f"{self.surface}{sep}{self.pos},{self.base_form},{self.reading}"


class SimpleTokenizer:
    """Lightweight character/word tokenizer."""

    def __init__(self, max_len: int = 1024, wakati: bool = False) -> None:
        """Initialize tokenizer.

        Args:
            max_len: Max allowed input string length (default 1024).
            wakati: If True, yield only surface strings.
        """
        self.max_len = max_len
        self.wakati = wakati

    def tokenize(self, text: str) -> list[Token]:
        """Tokenize text into list of Tokens."""
        if len(text) > self.max_len:
            raise ValueError(f"Input text exceeds max_len of {self.max_len}")
        tokens = []
        for word in text.split():
            tokens.append(Token(surface=word, pos="名詞", base_form=word))
        return tokens
