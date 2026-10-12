"""Tests for Uzbek Latin text normalization and sentence chunking (VC-034, VC-035)."""

from inference.app.core.text_normalizer import UzbekTextNormalizer, number_to_uzbek_words


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


def test_expand_numbers_in_text():
    """Verify numbers inside sentences are converted into spoken words."""
    text = "Bugun 12 aprel, harorat 25 daraja."
    norm = UzbekTextNormalizer.expand_numbers(text, language="uz")
    assert "o‘n ikki" in norm
    assert "yigirma besh" in norm


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
