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



# ---------------------------------------------------------------------------
# Short-title quoting
# ---------------------------------------------------------------------------

def test_short_title_without_colon_is_quoted():
    """
    KAŞİF's default search is keyword AND, not phrase. For a short
    title made of common words, the AND query returns too many records
    and the target is buried beyond the first page. Phrase search
    (quotes) returns the book directly.

    Real case: "Fark ve tekrar" (Deleuze, Norgunk 2017) is in KAŞİF
    but is not found without quotes.
    """
    ref = _turkish_book("Fark ve tekrar")
    url = primary_search_url(ref)

    assert url is not None
    assert "%22Fark%20ve%20tekrar%22" in url, (
        f"short title must be quoted: {url!r}"
    )


def test_long_title_without_colon_is_not_quoted():
    """
    Contract guard: a title long enough to be distinctive on its own
    must remain unquoted, as it is today.
    """
    ref = _turkish_book(
        "Osmanlı musikisinin tarihsel dönüşümü ve kurumsal "
        "kodifikasyon süreçleri"
    )
    url = primary_search_url(ref)

    assert url is not None
    assert "%22" not in url, f"long title must not be quoted: {url!r}"


def test_short_title_with_colon_is_not_quoted():
    """
    Contract guard: a colon in the title always wins over the short-
    title rule. Phrase search on a subtitle-bearing title risks failure
    if the catalog stores the subtitle differently.
    """
    ref = _turkish_book("Aşk: Bir hikâye")
    url = primary_search_url(ref)

    assert url is not None
    assert "%22" not in url, f"colon title must not be quoted: {url!r}"
    assert "%3A" not in url, f"colon must be literal: {url!r}"
    assert "%C5%9Fk:" in url, f"colon must be literal: {url!r}"

def test_short_title_without_common_word_is_not_quoted():
    """
    Contract guard for the narrow rule: a short title made of
    distinctive words searches fine unquoted, and phrase search could
    fail if the catalog stores internal punctuation differently.
    """
    ref = _turkish_book("Türk Mûsıkîsinin Mes'eleleri")
    url = primary_search_url(ref)

    assert url is not None
    assert "%22" not in url, f"distinctive short title must not be quoted: {url!r}"