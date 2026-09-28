"""
Tests for search-engine URL routing for unverified references.

The verification cascade labels some references as MANUAL_REVIEW or
NOT_FOUND. For those, we pick a search engine based on the reference's
likely language and type:

- Turkish thesis      -> YÖK Tez search page
- Turkish (other)     -> Milli Kütüphane KAŞİF, query pre-filled
- Everything else     -> Google Scholar, query pre-filled
"""

from models import Reference
from verification.search_links import (
    is_thesis_looking,
    is_turkish_looking,
    primary_search_url,
    search_link_label,
)


# --- is_turkish_looking -------------------------------------------------

def test_turkish_char_marks_reference_turkish():
    ref = Reference(raw_text="Tanyeli, U. (2017). Yıkarak yapmak. Metis.")
    assert is_turkish_looking(ref) is True


def test_turkish_translator_marker_marks_reference_turkish():
    ref = Reference(
        raw_text="Assmann, J. (2011). Kulturel bellek (A. Tekin, Çev.). Ayrinti."
    )
    assert is_turkish_looking(ref) is True


def test_english_reference_with_umlaut_is_not_turkish():
    # o-umlaut and u-umlaut appear in German and English loanwords,
    # so we deliberately exclude them from the Turkish character set.
    ref = Reference(
        raw_text="Schrodinger, E. (1935). The present situation in quantum mechanics."
    )
    assert is_turkish_looking(ref) is False


def test_plain_english_reference_is_not_turkish():
    ref = Reference(
        raw_text="Brown, B. (2001). Thing theory. Critical Inquiry, 28(1), 1-22."
    )
    assert is_turkish_looking(ref) is False


def test_empty_reference_is_not_turkish():
    assert is_turkish_looking(Reference(raw_text="")) is False


# --- is_thesis_looking --------------------------------------------------

def test_thesis_word_marks_thesis():
    ref = Reference(
        raw_text="Yilmaz, A. (2010). Yayimlanmamis yuksek lisans tezi."
    )
    assert is_thesis_looking(ref) is True


def test_degree_and_institute_mark_thesis():
    ref = Reference(
        raw_text="X Universitesi Sosyal Bilimler Enstitusu, Doktora Tezi."
    )
    assert is_thesis_looking(ref) is True


def test_surname_starting_with_tez_is_not_thesis():
    # Tezcan is a Turkish surname; it must not trigger the thesis check.
    ref = Reference(raw_text="Tezcan, N. (1997). Osmanli sarayi. Istanbul.")
    assert is_thesis_looking(ref) is False


def test_plain_book_is_not_thesis():
    ref = Reference(raw_text="Tanyeli, U. (2017). Yikarak yapmak. Metis.")
    assert is_thesis_looking(ref) is False


# --- primary_search_url -------------------------------------------------

def test_turkish_thesis_goes_to_yok_tez():
    ref = Reference(
        raw_text=(
            "Yilmaz, A. (2010). Sehir ve kimlik "
            "(Yayimlanmamis yuksek lisans tezi). Istanbul Universitesi."
        )
    )
    url = primary_search_url(ref)
    assert url == "https://tez.yok.gov.tr/UlusalTezMerkezi/tarama.jsp"


def test_turkish_book_goes_to_kasif_with_query():
    ref = Reference(
        raw_text=(
            "Tanyeli, U. (2017). Yıkarak yapmak: Mimarlık eyleminin "
            "modernliği üzerine. Metis Yayınları."
        )
    )
    url = primary_search_url(ref)
    assert url is not None
    assert url.startswith("https://kasif.mkutup.gov.tr/OpacArama.aspx?")
    assert "Ara=" in url
    assert "DtSrc=0" in url
    assert "fld=-1" in url
    assert "NvBar=0" in url


def test_non_turkish_goes_to_google_scholar():
    ref = Reference(
        title="Thing theory",
        raw_text=(
            "Brown, B. (2001). Thing theory. Critical Inquiry, 28(1), 1-22."
        ),
    )
    url = primary_search_url(ref)
    assert url is not None
    assert url.startswith("https://scholar.google.com/scholar?q=")
    assert "%22Thing%20theory%22" in url


def test_kasif_query_is_quoted_and_encoded():
    ref = Reference(
        title="Türk Mûsıkîsinin Mes'eleleri",
        raw_text="Tura, Y. (1988). Türk Mûsıkîsinin Mes'eleleri. Pan.",
    )
    url = primary_search_url(ref)
    assert url is not None
    assert "%22T%C3%BCrk%20M%C3%BBs%C4%B1k%C3%AEsinin" in url


def test_returns_none_when_no_title_or_text():
    assert primary_search_url(Reference(raw_text="")) is None

# --- search_link_label --------------------------------------------------

def test_label_for_kasif():
    url = (
        "https://kasif.mkutup.gov.tr/OpacArama.aspx?Ara=%22x%22"
        "&DtSrc=0&fld=-1&NvBar=0"
    )
    assert search_link_label(url) == "Search KAŞİF"


def test_label_for_yok_tez():
    url = "https://tez.yok.gov.tr/UlusalTezMerkezi/tarama.jsp"
    assert search_link_label(url) == "Search YÖK Tez"


def test_label_for_google_scholar():
    url = "https://scholar.google.com/scholar?q=test"
    assert search_link_label(url) == "Google Scholar"


def test_label_for_none_returns_generic():
    assert search_link_label(None) == "Search"


def test_label_for_unknown_url_returns_generic():
    assert search_link_label("https://example.com/search?q=x") == "Search"