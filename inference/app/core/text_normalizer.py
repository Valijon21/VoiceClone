"""Text normalization and chunking engine with first-class Uzbek Latin support."""

import re
from typing import Final

# Uzbek Number Pronunciation Dictionary
UZ_ONES: Final[dict[int, str]] = {
    0: "nol",
    1: "bir",
    2: "ikki",
    3: "uch",
    4: "to‘rt",
    5: "besh",
    6: "olti",
    7: "yetti",
    8: "sakkiz",
    9: "to‘qqiz",
}

UZ_TENS: Final[dict[int, str]] = {
    10: "o‘n",
    20: "yigirma",
    30: "o‘ttiz",
    40: "qirq",
    50: "ellik",
    60: "oltmish",
    70: "yetmish",
    80: "sakson",
    90: "to‘qson",
}


def number_to_uzbek_words(n: int) -> str:
    """Convert an integer (0 to 999,999,999) into standard Uzbek Latin words."""
    if n < 0:
        return f"minus {number_to_uzbek_words(abs(n))}"
    if n in UZ_ONES:
        return UZ_ONES[n]
    if n in UZ_TENS:
        return UZ_TENS[n]

    if n < 100:
        tens = (n // 10) * 10
        ones = n % 10
        return f"{UZ_TENS[tens]} {UZ_ONES[ones]}"

    if n < 1000:
        hundreds = n // 100
        remainder = n % 100
        h_str = "bir yuz" if hundreds == 1 else f"{UZ_ONES[hundreds]} yuz"
        if remainder == 0:
            return h_str
        return f"{h_str} {number_to_uzbek_words(remainder)}"

    if n < 1_000_000:
        thousands = n // 1000
        remainder = n % 1000
        t_str = "bir ming" if thousands == 1 else f"{number_to_uzbek_words(thousands)} ming"
        if remainder == 0:
            return t_str
        return f"{t_str} {number_to_uzbek_words(remainder)}"

    if n < 1_000_000_000:
        millions = n // 1_000_000
        remainder = n % 1_000_000
        m_str = f"{number_to_uzbek_words(millions)} million"
        if remainder == 0:
            return m_str
        return f"{m_str} {number_to_uzbek_words(remainder)}"

    return str(n)


class UzbekTextNormalizer:
    """Normalizes Uzbek Latin text, resolving apostrophes, numbers, and sentence chunking."""

    # All non-standard single quote variants to unify
    _APOSTROPHE_VARIANTS = re.compile(r"[`ʼ’‘´ʻ]")

    @classmethod
    def normalize_apostrophes(cls, text: str) -> str:
        """Unify varied unicode apostrophes in Uzbek Latin (o‘, g‘, tutuq belgisi)."""
        # 1. Standardize all variants following o/g to canonical '‘'
        text = re.sub(r"([oO])[`ʼ’‘´ʻ']", r"\1‘", text)
        text = re.sub(r"([gG])[`ʼ’‘´ʻ']", r"\1‘", text)
        # 2. Remaining single quote variants (tutuq belgisi e.g. ma'lumot) -> "'"
        text = re.sub(r"[`ʼ’´ʻ]", "'", text)
        return text

    @classmethod
    def expand_numbers(cls, text: str, language: str = "uz") -> str:
        """Convert standalone digits into textual word representations."""
        if language != "uz":
            return text

        def _replace_match(match: re.Match) -> str:
            val_str = match.group(0)
            try:
                num = int(val_str)
                return number_to_uzbek_words(num)
            except ValueError:
                return val_str

        return re.sub(r"\b\d+\b", _replace_match, text)

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Clean extra whitespaces, unsupported non-printable symbols."""
        if not text:
            return ""
        # Remove control characters except standard punctuation and newlines
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Normalize multiple spaces and tabs to single space
        text = re.sub(r"[ \t]+", " ", text)
        # Normalize multiple newlines
        text = re.sub(r"\n{2,}", "\n", text)
        return text.strip()

    @classmethod
    def normalize(cls, text: str, language: str = "uz") -> str:
        """Run complete normalization pipeline."""
        if not text:
            return ""
        cleaned = cls.clean_text(text)
        if language == "uz":
            cleaned = cls.normalize_apostrophes(cleaned)
            cleaned = cls.expand_numbers(cleaned, language="uz")
        return cleaned

    @classmethod
    def chunk_text(cls, text: str, max_chars: int = 250) -> list[str]:
        """Split text into sentence-bounded chunks respecting the maximum character limit."""
        if not text:
            return []

        # Split on sentence boundaries: periods, exclamation, question marks, newlines
        raw_sentences = re.split(r"(?<=[.!?\n])\s+", text)
        chunks: list[str] = []
        current_chunk = ""

        for sentence in raw_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(sentence) > max_chars:
                # If a single sentence exceeds max_chars, split on commas or spaces
                sub_parts = re.split(r"(?<=[,;:])\s+", sentence)
                for part in sub_parts:
                    if len(current_chunk) + len(part) + 1 <= max_chars:
                        current_chunk = f"{current_chunk} {part}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = part
            elif len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk = f"{current_chunk} {sentence}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
