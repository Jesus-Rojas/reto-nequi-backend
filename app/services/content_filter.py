import re

# Words that will be censored. Extend this list as needed.
_FORBIDDEN_WORDS: list[str] = [
    # English
    "spam", "scam", "offensive", "inappropriate",
    # Spanish
    "idiota", "imbecil", "estupido", "maldito", "mierda", "basura", "inutil",
]


class ContentFilterService:
    """Detects and redacts inappropriate content from message text."""

    def __init__(self, forbidden_words: list[str] | None = None):
        source = forbidden_words if forbidden_words is not None else _FORBIDDEN_WORDS
        # Pre-compile one pattern per word for efficiency
        self._patterns: list[tuple[re.Pattern, str]] = [
            (re.compile(re.escape(w), re.IGNORECASE), "*" * len(w))
            for w in source
        ]

    def contains_inappropriate_content(self, content: str) -> bool:
        return any(p.search(content) for p, _ in self._patterns)

    def filter_content(self, content: str) -> tuple[str, bool]:
        """Return *(filtered_content, was_filtered)*."""
        result = content
        filtered = False
        for pattern, replacement in self._patterns:
            new_result, count = pattern.subn(replacement, result)
            if count:
                result = new_result
                filtered = True
        return result, filtered
