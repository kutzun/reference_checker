"""
Tests for article routing in search_links.

KAŞİF catalogues whole serials, not individual articles. Every journal
article must route to Google Scholar regardless of the journal's name
or language.

The existing heuristics miss journals whose name does not contain one
of the hard-coded keywords (Journal, Review, Bulletin, Quarterly,
Annals, Proceedings) and that use APA volume(issue) notation instead
of the spelled-out "Cilt N ... Sayı N" form. A Turkish-language
journal article in such a journal currently routes to KAŞİF, where it
cannot be found.
"""

from models import Reference
from verification.search_links import (
    is_article_looking,
    primary_search_url,
)


def _ref(title: str, raw: str) -> Reference:
    return Reference(title=title, raw_text=raw)


def test_apa_volume_issue_marker_detects_article():
    """
    'Social Sciences Studies, 11(8), 1380-1382' is a journal article
    in APA format. Journal name contains no keyword from
    _ARTICLE_MARKERS, and the volume/issue uses parenthesized APA
    notation, not the spelled-out Turkish form.
    """
    ref = _ref(
        "Sanatta Yapay Zeka ve Bir Öncü: Refik Anadol'un Veri Estetiği",
        "Büyükkaragöz, T. (2025). Sanatta Yapay Zeka ve Bir Öncü: "
        "Refik Anadol'un Veri Estetiği. Social Sciences Studies, "
        "11(8), 1380-1382, 1386-1389.",
    )
    assert is_article_looking(ref) is True


def test_turkish_journal_article_routes_to_scholar():
    """
    A Turkish-language journal article must not route to KAŞİF. KAŞİF
    holds the serial, not the article inside it.
    """
    ref = _ref(
        "Sanatta Yapay Zeka ve Bir Öncü: Refik Anadol'un Veri Estetiği",
        "Büyükkaragöz, T. (2025). Sanatta Yapay Zeka ve Bir Öncü: "
        "Refik Anadol'un Veri Estetiği. Social Sciences Studies, "
        "11(8), 1380-1382, 1386-1389.",
    )
    url = primary_search_url(ref)
    assert url is not None
    assert "scholar.google.com" in url, (
        f"journal article must route to Scholar, got {url!r}"
    )


def test_apa_volume_issue_english_journal_detects_article():
    """Same signal, journal name entirely in English."""
    ref = _ref(
        "Some title",
        "Smith, J. (2020). Some title. Nature, 580(7801), 100-105.",
    )
    assert is_article_looking(ref) is True


# ---------------------------------------------------------------------------
# Contract guards
# ---------------------------------------------------------------------------

def test_turkish_book_still_routes_to_kasif():
    ref = _ref(
        "Makam: Türk Sanat Musikisinde Makam Uygulaması",
        "Signell, K. L. (2006). Makam: Türk Sanat Musikisinde Makam "
        "Uygulaması. Yapı Kredi Yayınları.",
    )
    url = primary_search_url(ref)
    assert url is not None
    assert "kasif.mkutup.gov.tr" in url


def test_english_book_routes_to_scholar():
    ref = _ref(
        "Managing emergent phenomena",
        "Guastello, S. J. (2002). Managing emergent phenomena. "
        "Lawrence Erlbaum Associates.",
    )
    url = primary_search_url(ref)
    assert url is not None
    assert "scholar.google.com" in url


def test_existing_journal_keyword_still_works():
    """Contract guard: the pre-existing article heuristics must not
    regress."""
    ref = _ref(
        "Some article",
        "Smith, J. (2020). Some article. Journal of Examples, 1(1), 1-10.",
    )
    assert is_article_looking(ref) is True