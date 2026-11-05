"""
Tests for orphan-paren detection in the in-text extractor.

Regression for 44.docx / Keskin 2009 and Özgüç 1980: when a citation
contains a nested parenthesis - balanced (``(A, 1980 (see X))``) or
unbalanced (``(A, 1980 (X)`` with no close on the outer) - the outer
parens are skipped by the well-formed regex, and the citation content
is silently lost. The extractor now flags such orphan opens as
Unparsed so editors can see them.
"""

from __future__ import annotations

from internal_check.intext_extractor import InTextExtractor
from internal_check.profiles import ENGLISH


KESKIN_PARAGRAPH = (
    "Daha sonraki dönemlerde Sarıket Höyük'ü, (Fidan, 2005, s. 77 Fig. "
    "100-284), Bakla Tepe (Keskin, 2009, s. 219, 220 Fig. 16 ve İkiztepe "
    "(Bilgi, 1999, s. 48 Fig. 19-48) buluntuları söz konusu bilezik "
    "tipinin Erken Tunç Çağ II ve III'de yaygın olarak kullanıldığı "
    "göstermektedir."
)
OZGUC_PARAGRAPH = (
    "Benzer örnekler, Çorum çevresindeki Yenihayat (Özgüç, 1980, s. 465; "
    "Müller-Karpe, 1994, Taf.91/16 (Yenihayat), Taf.96/B3,4 Mecitözü) ve "
    "Mecitözü (Özgüç, 1978, s. 34; Müller-Karpe, 1994, Taf.96/A1,Taf.96/"
    "C1 Merzifon)."
)


def test_keskin_unbalanced_nested_flagged() -> None:
    extractor = InTextExtractor(ENGLISH)
    extractor.extract([KESKIN_PARAGRAPH])
    texts = [t for t, _ in extractor.unparsed]
    assert any("Keskin" in t for t in texts), texts


def test_ozguc_balanced_nested_flagged() -> None:
    extractor = InTextExtractor(ENGLISH)
    extractor.extract([OZGUC_PARAGRAPH])
    texts = [t for t, _ in extractor.unparsed]
    assert any("Özgüç, 1980" in t for t in texts), texts


def test_no_flag_for_well_formed_citation() -> None:
    extractor = InTextExtractor(ENGLISH)
    extractor.extract(["Pro-environmental behaviour (Steg & Vlek, 2009)."])
    assert extractor.unparsed == []


def test_no_flag_for_page_locator() -> None:
    extractor = InTextExtractor(ENGLISH)
    extractor.extract(["Smith (2020, p. 1945) argued."])
    assert extractor.unparsed == []


def test_no_flag_for_nested_parens_without_year() -> None:
    extractor = InTextExtractor(ENGLISH)
    extractor.extract([
        "The result (p < 0.05 (two-tailed)) was significant."
    ])
    texts = [t for t, _ in extractor.unparsed]
    assert not any("p < 0.05" in t for t in texts), texts


def test_well_formed_paren_not_over_captured() -> None:
    """If a paren is consumed by the main regex, the orphan capture
    must not also fire and append a wider span. Pre-existing Case 2
    logic still flags '(the site)' as unparsed (no year); that is
    the only flag - no duplicate, and no over-capture past the
    closing paren."""
    extractor = InTextExtractor(ENGLISH)
    extractor.extract(["Yenihayat (the site) yielded similar examples."])
    texts = [t for t, _ in extractor.unparsed]
    assert texts == ["(the site)"], texts