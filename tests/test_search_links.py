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
    is_article_looking,
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


# --- (thesis detection was removed; see search_links.py) ----------------


# --- primary_search_url -------------------------------------------------

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

# --- Fix #1: strip Turkish access-date boilerplate ----------------------

def test_english_web_ref_with_erisim_tarihi_is_not_turkish():
    """A URL-only English reference with a Turkish access-date tail
    cites an English source. 'Erişim Tarihi' describes the citation
    style, not the language of the source."""
    ref = Reference(
        raw_text=(
            "Classical Music Daily, (t.y.). "
            "https://www.classicalmusicdaily.com/articles/o/w/woo.htm. "
            "Erişim Tarihi: 03.06.2026."
        )
    )
    assert is_turkish_looking(ref) is False


def test_english_ref_with_tarihinde_tail_is_not_turkish():
    ref = Reference(
        raw_text=(
            "Bis, German Music for Trombones. "
            "https://eclassical.textalk.se/shop/17175/art34/x.pdf "
            "Erişim Tarihi: 05.06.2026."
        )
    )
    assert is_turkish_looking(ref) is False


def test_turkish_book_still_detected_after_boilerplate_stripping():
    """After stripping the access-date tail, the Turkish title
    characters must still trigger detection."""
    ref = Reference(
        raw_text=(
            "Tura, Y. (1988). Türk Mûsıkîsinin Mes'eleleri. Pan Yayıncılık. "
            "Erişim Tarihi: 05.06.2026."
        )
    )
    assert is_turkish_looking(ref) is True


# --- Fix #1: Turkish function words for diacritic-stripped titles -------

def test_diacritic_stripped_turkish_title_with_ve_is_turkish():
    ref = Reference(
        raw_text="Yikarak yapmak ve mimarlik eyleminin modernligi. Metis."
    )
    assert is_turkish_looking(ref) is True


def test_diacritic_stripped_turkish_title_with_ile_is_turkish():
    ref = Reference(
        raw_text="Sanat ile tasarim uzerine bir inceleme. Kabalci."
    )
    assert is_turkish_looking(ref) is True


def test_plain_english_ref_does_not_trigger_function_words():
    ref = Reference(
        raw_text="Brown, B. (2001). Thing theory. Critical Inquiry, 28(1), 1-22."
    )
    assert is_turkish_looking(ref) is False


# --- Fix #2: article detection ------------------------------------------

def test_dergisi_marks_article():
    ref = Reference(
        raw_text="Alpay, G. (1972). Baslik. Felsefe Dergisi, Sayi 10, 83-97."
    )
    assert is_article_looking(ref) is True


def test_quoted_title_marks_article():
    ref = Reference(
        raw_text='Kaçar, G. Y. (2008). "Türk Mûsikîsinde Makam", İstem, 6(11), 145-158.'
    )
    assert is_article_looking(ref) is True


def test_cilt_and_sayi_marks_article():
    ref = Reference(
        raw_text="Ornek, A. (2010). Baslik. Dergi, Cilt 3, Sayi 5, 10-20."
    )
    assert is_article_looking(ref) is True


def test_journal_in_english_marks_article():
    ref = Reference(
        raw_text=(
            "Wright, O. (1994). A Preliminary Version. "
            "Bulletin of the School of Oriental and African Studies, 58(3), 455-478."
        )
    )
    assert is_article_looking(ref) is True


def test_book_is_not_article():
    ref = Reference(
        raw_text="Tanyeli, U. (2017). Yıkarak yapmak. Metis Yayınları."
    )
    assert is_article_looking(ref) is False


def test_book_with_subtitle_is_not_article():
    ref = Reference(
        raw_text=(
            "Bardakçı, M. (1986). Maragalı Abdülkadir: Hayat Hikâyesi. "
            "Pan Yayıncılık."
        )
    )
    assert is_article_looking(ref) is False


# --- Fix #2: routing precedence -----------------------------------------

def test_thesis_markers_no_longer_route_to_yok_tez():
    """Thesis detection was removed: Turkish and foreign theses alike
    go to Google Scholar. A reference that contains both thesis and
    article markers therefore routes on the article branch."""
    ref = Reference(
        raw_text=(
            "Yilmaz, A. (2010). Baslik. Yayimlanmamis doktora tezi. "
            "Istanbul Universitesi. Felsefe Dergisi, Sayi 10."
        )
    )
    url = primary_search_url(ref)
    assert url is not None
    assert url.startswith("https://scholar.google.com/scholar?q=")


def test_turkish_article_routes_to_scholar_not_kasif():
    ref = Reference(
        raw_text=(
            'Kaçar, G. Y. (2008). "Türk Mûsikîsinde Makam", '
            "İstem, Cilt 6, Sayı 11, 145-158."
        )
    )
    url = primary_search_url(ref)
    assert url is not None
    assert url.startswith("https://scholar.google.com/scholar?q=")


def test_turkish_article_with_dergisi_routes_to_scholar():
    ref = Reference(
        raw_text="Alpay, G. (1972). Baslik. Felsefe Dergisi, Sayı 10, 83-97."
    )
    url = primary_search_url(ref)
    assert url is not None
    assert url.startswith("https://scholar.google.com/scholar?q=")


def test_turkish_book_still_routes_to_kasif():
    ref = Reference(
        raw_text="Tanyeli, U. (2017). Yıkarak yapmak. Metis Yayınları."
    )
    url = primary_search_url(ref)
    assert url is not None
    assert url.startswith("https://kasif.mkutup.gov.tr/OpacArama.aspx?")