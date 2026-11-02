"""
Tests for KAŞİF search URL construction.

KAŞİF (Milli Kütüphane) treats ':' as a field-separator operator in the
Ara= query parameter. A title containing a colon — common in Turkish
academic books, e.g. "Makam: Türk Sanat Musikisinde Makam Uygulaması" —
produces an unparseable query and returns no results, even when the
book is in the catalog.
"""

from models import Reference
from verification.search_links import primary_search_url


def _turkish_book(title: str) -> Reference:
    return Reference(
        raw_text=f"Signell, K. L., {title}, Yapı Kredi Yayınları, İstanbul 2006.",
        authors=["Signell"],
        title=title,
        publisher="Yapı Kredi Yayınları",
        year=2006,
    )


def test_kasif_query_has_no_colon():
    """
    A Turkish book title containing ':' must produce a KAŞİF URL with
    no %3A. Confirmed against a real manuscript: the same query with
    %3A returns zero hits, with a space returns the book.
    """
    ref = _turkish_book("Makam: Türk Sanat Musikisinde Makam Uygulaması")
    url = primary_search_url(ref)

    assert url is not None
    assert "kasif.mkutup.gov.tr" in url
    assert "%3A" not in url, f"colon leaked into KAŞİF query: {url!r}"
    assert "%3a" not in url, f"lowercase colon leaked: {url!r}"


def test_kasif_query_words_are_preserved():
    """
    Stripping the colon must not swallow the words on either side.
    Both 'Makam' (before the colon) and 'Türk' (after) must remain.
    """
    ref = _turkish_book("Makam: Türk Sanat Musikisinde Makam Uygulaması")
    url = primary_search_url(ref)

    assert url is not None
    assert "Makam" in url
    assert "T%C3%BCrk" in url or "Türk" in url


def test_kasif_query_has_no_double_spaces():
    """
    After removing the colon, a single space joins the two words —
    not a double space, which KAŞİF also dislikes.
    """
    ref = _turkish_book("Makam: Türk Sanat Musikisinde Makam Uygulaması")
    url = primary_search_url(ref)

    assert url is not None
    assert "%20%20" not in url, f"double space in KAŞİF query: {url!r}"