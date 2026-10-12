"""Tests for Uzbek Latin text normalization, ordinal expansion, and phonetic heuristics (VC-034, VC-092)."""

from inference.app.core.text_normalizer import (
    UzbekTextNormalizer,
    number_to_uzbek_ordinal_words,
    number_to_uzbek_words,
)


def test_number_to_uzbek_words():
    """Verify cardinal numbers are converted to correct Uzbek words."""
    assert number_to_uzbek_words(0) == "nol"
    assert number_to_uzbek_words(5) == "besh"
    assert number_to_uzbek_words(10) == "o‘n"
    assert number_to_uzbek_words(25) == "yigirma besh"
    assert number_to_uzbek_words(100) == "bir yuz"
    assert number_to_uzbek_words(105) == "bir yuz besh"
    assert number_to_uzbek_words(1991) == "bir ming to‘qqiz yuz to‘qson bir"
    assert number_to_uzbek_words(2026) == "ikki ming yigirma olti"


def test_number_to_uzbek_ordinal_words():
    """VC-092 / P1-1: Verify ordinal numbers are converted with correct suffixes."""
    assert number_to_uzbek_ordinal_words(1) == "birinchi"
    assert number_to_uzbek_ordinal_words(2) == "ikkinchi"
    assert number_to_uzbek_ordinal_words(5) == "beshinchi"
    assert number_to_uzbek_ordinal_words(6) == "oltinchi"
    assert number_to_uzbek_ordinal_words(10) == "o‘ninchi"
    assert number_to_uzbek_ordinal_words(20) == "yigirmanchi"
    assert number_to_uzbek_ordinal_words(2026) == "ikki ming yigirma oltinchi"


def test_normalize_uzbek_apostrophes():
    """Verify various unicode quotes are canonicalized into standard o‘ and g‘."""
    # Test o' variations
    variants = ["o`zbekiston", "o'zbekiston", "o’zbekiston", "o‘zbekiston"]
    for variant in variants:
        res = UzbekTextNormalizer.normalize_apostrophes(variant)
        assert res.startswith("o‘zbekiston"), f"Failed for {variant}"

    # Test g' variations
    g_variants = ["g`alaba", "g'alaba", "g’alaba", "g‘alaba"]
    for variant in g_variants:
        res = UzbekTextNormalizer.normalize_apostrophes(variant)
        assert res.startswith("g‘alaba"), f"Failed for {variant}"


def test_restore_missing_apostrophes():
    """VC-092 / P0-1, P0-2: Verify words typed without apostrophes are automatically fixed."""
    text = "ozbekiston va qoraqalpogiston boyicha talim va malumot tizimi"
    restored = UzbekTextNormalizer.restore_missing_apostrophes(text)
    assert "o‘zbekiston" in restored
    assert "ta'lim" in restored
    assert "ma'lumot" in restored

    # Case preservation
    title_text = "Ozbekiston Respublikasi"
    assert UzbekTextNormalizer.restore_missing_apostrophes(title_text).startswith("O‘zbekiston")


def test_expand_ordinals_and_percentages():
    """VC-092 / P1-1, P1-2: Verify year ordinals and percentages are naturally expanded."""
    text = "2026-yil 1-o‘rinni oldi va 50% chegirma berildi."
    expanded = UzbekTextNormalizer.expand_ordinals_and_percentages(text, language="uz")
    assert "ikki ming yigirma oltinchi yil" in expanded
    assert "birinchi o‘rinni" in expanded
    assert "ellik foiz" in expanded


def test_loanwords_and_abbreviations():
    """VC-092 / P1-4, P2-1: Verify loanwords and standard abbreviations are phonetized."""
    text = "Biz YouTube va Python orqali dars o'tamiz, va h.k."
    loan_norm = UzbekTextNormalizer.normalize_loanwords(text)
    assert "Yutub" in loan_norm
    assert "Payton" in loan_norm

    abbr_norm = UzbekTextNormalizer.expand_abbreviations(text)
    assert "va hokazo" in abbr_norm


def test_end_to_end_advanced_normalization():
    """VC-092: Test complete normalization pipeline with all P0/P1/P2 fixes combined."""
    input_text = "Ozbekistonda 2026-yil talim sifati 85% ga yetdi, mas. YouTube darslari."
    output = UzbekTextNormalizer.normalize(input_text, language="uz")
    assert "O‘zbekistonda" in output
    assert "ikki ming yigirma oltinchi yil" in output
    assert "ta'lim" in output
    assert "sakson besh foiz" in output
    assert "masalan" in output
    assert "Yutub" in output


def test_text_chunking():
    """Verify text is chunked cleanly without breaking sentences when under limit."""
    long_text = (
        "Birinchi jumla juda chiroyli va mazmunli yangraydi. "
        "Ikkinchi jumla ham o‘z navbatida muhim fikrlarni ifodalaydi. "
        "Uchinchi jumla esa xulosa sifatida xizmat qiladi."
    )
    chunks = UzbekTextNormalizer.chunk_text(long_text, max_chars=80)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 100
        assert chunk.strip() != ""
