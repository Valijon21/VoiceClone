"""Text normalization and chunking engine with first-class Uzbek Latin support."""

from __future__ import annotations

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

# Stem replacements for words frequently typed without apostrophes (VC-092 / P0-1, P0-2)
COMMON_STEM_REPLACEMENTS: Final[dict[str, str]] = {
    "ozbek": "o‘zbek",
    "oqituvchi": "o‘qituvchi",
    "oqish": "o‘qish",
    "oqimoq": "o‘qimoq",
    "ogil": "o‘g‘il",
    "oglim": "o‘g‘lim",
    "qoriqchi": "qo‘riqchi",
    "malumot": "ma'lumot",
    "talim": "ta'lim",
    "etibor": "e'tibor",
    "sanat": "san'at",
    "tasir": "ta'sir",
    "masul": "mas'ul",
    "elon": "e'lon",
    "mojiza": "mo‘jiza",
    "songra": "so‘ngra",
    "songgi": "so‘nggi",
    "ortada": "o‘rtada",
    "ogir": "o‘g‘ir",
}

EXACT_WORD_REPLACEMENTS: Final[dict[str, str]] = {
    "tog": "tog‘",
    "bog": "bog‘",
    "song": "so‘ng",
    "kop": "ko‘p",
    "qol": "qo‘l",
    "yol": "yo‘l",
    "orta": "o‘rta",
    "ogir": "o‘g‘ir",
}

SHORT_STEM_REPLACEMENTS: Final[dict[str, str]] = {
    "tog": "tog‘",
    "bog": "bog‘",
    "qol": "qo‘l",
    "yol": "yo‘l",
    "bol": "bo‘l",
    "kor": "ko‘r",
    "kop": "ko‘p",
}

# Popular tech and media loanwords to phonetic spellings (VC-092 / P1-4)
LOANWORD_PHONETICS: Final[dict[str, str]] = {
    "youtube": "yutub",
    "telegram": "telegram",
    "python": "payton",
    "google": "gugl",
    "ai": "ey ay",
    "it": "ay ti",
    "chatgpt": "chat jipiti",
}

# Standard Uzbek abbreviations (VC-092 / P2-1)
ABBREVIATIONS_MAP: Final[dict[str, str]] = {
    r"\bva h\.k\b\.?": "va hokazo",
    r"\bva boshq\b\.?": "va boshqalar",
    r"\bmas\b\.": "masalan",
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


def number_to_uzbek_ordinal_words(n: int) -> str:
    """Convert an integer into an ordinal word (e.g. 2026 -> ikki ming yigirma oltinchi)."""
    cardinal = number_to_uzbek_words(n)
    if cardinal.endswith(("i", "a")):
        return f"{cardinal}nchi"
    return f"{cardinal}inchi"


class UzbekTextNormalizer:
    """Normalizes Uzbek Latin text, resolving apostrophes, numbers, and sentence chunking."""

    _APOSTROPHE_VARIANTS = re.compile(r"[`ʼ’‘´ʻ]")

    @staticmethod
    def _match_case(original: str, replacement: str) -> str:
        """Preserve original casing (e.g. Ozbekiston -> O‘zbekiston)."""
        if original.isupper():
            return replacement.upper()
        if original[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement

    @classmethod
    def restore_missing_apostrophes(cls, text: str) -> str:
        """Heuristically restore missing apostrophes for the most common ambiguous words (VC-092 / P0-1)."""
        valid_suffixes = (
            "da", "dan", "ga", "ni", "ning", "lar", "larga", "larda", "lardan",
            "i", "im", "ing", "imiz", "ingiz", "di", "gan", "sa", "moq", "ish",
            "dim", "dik", "dilar", "aylik", "cha", "dek"
        )

        def _replace_word(match: re.Match) -> str:
            word = match.group(0)
            low = word.lower()

            # 1. Exact match
            if low in EXACT_WORD_REPLACEMENTS:
                return cls._match_case(word, EXACT_WORD_REPLACEMENTS[low])

            # 2. Check stem replacements (e.g. ozbekistonda -> o‘zbekistonda)
            for stem, rep_stem in COMMON_STEM_REPLACEMENTS.items():
                if low.startswith(stem):
                    suffix = low[len(stem):]
                    rep = rep_stem + suffix
                    return cls._match_case(word, rep)

            # 3. Check short stems with common suffixes (e.g. togda -> tog‘da)
            for stem, rep_stem in SHORT_STEM_REPLACEMENTS.items():
                if low.startswith(stem):
                    suffix = low[len(stem):]
                    if not suffix or suffix in valid_suffixes:
                        rep = rep_stem + suffix
                        return cls._match_case(word, rep)

            return word

        return re.sub(r"\b[a-zA-Z‘'ʼ`´ʻ]+\b", _replace_word, text)

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
    def normalize_loanwords(cls, text: str) -> str:
        """Phonetize common foreign IT and media loanwords for natural spoken reading (VC-092 / P1-4)."""
        def _replace_loanword(match: re.Match) -> str:
            word = match.group(0)
            low = word.lower()
            if low in LOANWORD_PHONETICS:
                phonetic = LOANWORD_PHONETICS[low]
                if word[0].isupper():
                    return phonetic.capitalize()
                return phonetic
            return word

        return re.sub(r"\b[a-zA-Z0-9]+\b", _replace_loanword, text)

    @classmethod
    def expand_abbreviations(cls, text: str) -> str:
        """Expand common abbreviations into full spoken words (VC-092 / P2-1)."""
        for pattern, replacement in ABBREVIATIONS_MAP.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    @classmethod
    def expand_ordinals_and_percentages(cls, text: str, language: str = "uz") -> str:
        """Expand percentages (50%) and ordinal numbers (2026-yil, 1-o‘rin)."""
        if language != "uz":
            return text

        # Percentages: 50% -> ellik foiz
        def _replace_pct(match: re.Match) -> str:
            num_str = match.group(1)
            try:
                num = int(num_str)
                return f"{number_to_uzbek_words(num)} foiz"
            except ValueError:
                return match.group(0)

        text = re.sub(r"\b(\d+)\s*%", _replace_pct, text)

        # Ordinals: 2026-yil, 1-o'rinni, 5-sinf
        def _replace_ordinal(match: re.Match) -> str:
            num_str = match.group(1)
            noun = match.group(2)
            try:
                num = int(num_str)
                ord_word = number_to_uzbek_ordinal_words(num)
                noun_norm = cls.normalize_apostrophes(noun)
                return f"{ord_word} {noun_norm}"
            except ValueError:
                return match.group(0)

        ordinal_regex = r"\b(\d+)-(yil[a-z]*|sinf[a-z]*|o[‘'`]rin[a-z]*|qavat[a-z]*|dars[a-z]*|bob[a-z]*|modda[a-z]*|kun[a-z]*|oy[a-z]*)\b"
        text = re.sub(ordinal_regex, _replace_ordinal, text, flags=re.IGNORECASE)

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
            cleaned = cls.restore_missing_apostrophes(cleaned)
            cleaned = cls.normalize_apostrophes(cleaned)
            cleaned = cls.expand_abbreviations(cleaned)
            cleaned = cls.normalize_loanwords(cleaned)
            cleaned = cls.expand_ordinals_and_percentages(cleaned, language="uz")
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
