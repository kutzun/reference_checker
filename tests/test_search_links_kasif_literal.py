"""
Tests for literal colon and comma handling in KAŞİF search URLs.

KAŞİF accepts literal ':' and ',' in the Ara= query parameter. Encoded
forms (%3A, %2C) are treated as field separators or as distinct tokens
and cause the search to return no results for titles that contain
either character.

Evidence: for "Kültürel bellek: Eski yüksek kültürlerde yazı, hatırlama
ve politik kimlik", an app link with the colon stripped and the comma
encoded returns zero hits; the same title pasted manually (literal ':'
and ',') returns the book.
"""

from models import Reference
from verification.search_links import primary_search_url


def _turkish_book(title: str) -> Reference:
    return Reference(
        raw_text=f"Author, A., {title}, Publisher, İstanbul 2020.",
        authors=["Author"],
        title=title,
        publisher="Publisher",
        year=2020,
    )


def test_colon_and_comma_left_literal():
    ref = _turkish_book(
        "Kültürel bellek: Eski yüksek kültürlerde yazı, hatırlama ve "
        "politik kimlik"
    )
    url = primary_search_url(ref)

    assert url is not None
    assert "kasif.mkutup.gov.tr" in url
    assert "bellek:%20" in url, f"colon must be literal: {url!r}"
    assert "bellek%3A" not in url, f"colon must not be encoded: {url!r}"
    assert "yaz%C4%B1,%20" in url, f"comma must be literal: {url!r}"
    assert "yaz%C4%B1%2C" not in url, f"comma must not be encoded: {url!r}"


def test_makam_title_uses_literal_colon():
    ref = _turkish_book("Makam: Türk Sanat Musikisinde Makam Uygulaması")
    url = primary_search_url(ref)

    assert url is not None
    assert "Makam:%20" in url, f"colon must be literal: {url!r}"
    assert "Makam%3A" not in url, f"colon must not be encoded: {url!r}"
    assert "Makam%20T" not in url, f"colon must not be stripped: {url!r}"


def test_colon_free_title_unchanged():
    ref = _turkish_book("Fark ve tekrar")
    url = primary_search_url(ref)

    assert url is not None
    assert "Fark%20ve%20tekrar" in url