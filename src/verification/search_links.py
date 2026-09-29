"""
Pick the best search engine for a reference that failed verification.

Different reference types benefit from different search engines:

- Journal articles are best found on Google Scholar regardless of
  language. Milli Kütüphane's KAŞİF catalogues whole serials, not the
  individual articles inside them.
- Turkish-language monographs are best found on KAŞİF, which holds
  every book published in Turkey since 1934.
- Everything else, including theses in any language, goes to Google
  Scholar. Theses are deliberately not routed to YÖK Ulusal Tez
  Merkezi: that archive holds only theses defended at Turkish
  universities, so a foreign dissertation would be sent to a catalog
  that cannot contain it.

This module is pure: it performs no I/O and imports nothing from the
verification providers.
"""

from __future__ import annotations

import re
from urllib.parse import quote

from models import Reference


# Characters that are essentially unique to Turkish. Deliberately
# excludes o-umlaut and u-umlaut, which appear in German and in English
# loanwords (Schrodinger, facade, Mobius) and would produce false
# positives on genuinely non-Turkish references.
_TURKISH_CHARS = frozenset("çÇğĞıİşŞ")

# Turkish-to-ASCII folding table used for keyword matching, so that
# markers written with or without diacritics match the same pattern.
_FOLD = str.maketrans({
    "ı": "i", "İ": "i",
    "ğ": "g", "Ğ": "g",
    "ş": "s", "Ş": "s",
    "ç": "c", "Ç": "c",
    "ö": "o", "Ö": "o",
    "ü": "u", "Ü": "u",
})

# Turkish-only citation boilerplate that appears in the reference but
# describes the citation style, not the language of the cited source.
# "Classical Music Daily. https://... Erişim Tarihi: 03.06.2026" is an
# English source cited in Turkish APA style, not a Turkish reference.
_BOILERPLATE_TAIL = re.compile(
    r"erisim tarihi\s*:.*$"           # "Erişim Tarihi: ..."
    r"|tarihinde\b.*?erisim\b.*$"     # "tarihinde ... erişim sağlanmıştır"
    r"|adresinden\b.*$",              # "adresinden alındı"
    re.IGNORECASE | re.DOTALL,
)

# Turkish standalone function words. These are the markers that survive
# when an author has stripped diacritics (writing "yikarak yapmak"
# instead of "yıkarak yapmak"). Selected to have almost no collisions
# with English surnames or common English words.
_TURKISH_FUNCTION_WORDS = re.compile(
    r"\b("
    r"ve|ile|gibi|dair|olarak|kadar|dahil|uzere|uzerine"
    r"|hakkinda|tarafindan|arasinda|yoluyla|sebebiyle"
    r")\b",
    re.IGNORECASE,
)

# Structural markers that reliably indicate a Turkish-language citation.
_TURKISH_MARKERS = re.compile(
    r"\byayinlari\b|\byayinevi\b|\bbasimevi\b|\bkitabevi\b|\bdergisi\b"
    r"|\bcilt\b|\bsayi\b|\bcev\b|\bhaz\b"
)

# Markers that indicate a journal article or a chapter in an edited
# volume, rather than a standalone book. Journal article titles in APA
# are typically wrapped in double quotes; books are not. Volume-plus-
# issue is a serial-only pattern. And a handful of journal-name words
# are essentially universal across languages.
_ARTICLE_MARKERS = re.compile(
    r"\bdergisi\b|\bjournal\b|\breview\b|\bbulletin\b|\bquarterly\b"
    r"|\bannals\b|\bproceedings\b"
)

_ARTICLE_QUOTED_TITLE = re.compile(r"[\"“”][^\"“”]{10,}[\"“”]")

_ARTICLE_CILT_SAYI = re.compile(
    r"\bcilt\b[\s\S]{0,20}\bsayi\b|\bvolume\b[\s\S]{0,20}\bissue\b",
    re.IGNORECASE,
)


def _fold(s: str) -> str:
    """Lower-case *s* and normalise Turkish characters to ASCII."""
    return s.translate(_FOLD).lower()


def _reference_text(reference: Reference) -> str:
    """Concatenate the fields we use for heuristics."""
    parts = []
    if reference.title:
        parts.append(reference.title)
    if reference.raw_text:
        parts.append(reference.raw_text)
    return " ".join(parts)


def _strip_boilerplate(text: str) -> str:
    """
    Remove Turkish citation boilerplate that describes the citation
    style rather than the language of the cited source.

    Called before language detection so that an English URL-only
    reference does not get classified as Turkish merely because the
    author appended "Erişim Tarihi: ..." to it.
    """
    folded = _fold(text)
    match = _BOILERPLATE_TAIL.search(folded)
    if match:
        return text[: match.start()]
    return text


def is_turkish_looking(reference: Reference) -> bool:
    """True if the reference looks like it cites a Turkish-language source."""
    text = _reference_text(reference)
    if not text:
        return False

    stripped = _strip_boilerplate(text)

    if any(c in _TURKISH_CHARS for c in stripped):
        return True

    folded = _fold(stripped)
    if _TURKISH_MARKERS.search(folded):
        return True
    if _TURKISH_FUNCTION_WORDS.search(folded):
        return True

    return False


def is_article_looking(reference: Reference) -> bool:
    """
    True if the reference looks like a journal article or a chapter in
    an edited volume, rather than a standalone monograph.

    Deliberately language-independent: an article in an English journal
    is just as much an "article" as one in a Turkish Dergisi, and the
    routing outcome (Scholar) is the same for both.
    """
    text = _reference_text(reference)
    if not text:
        return False

    if _ARTICLE_MARKERS.search(_fold(text)):
        return True
    if _ARTICLE_QUOTED_TITLE.search(text):
        return True
    if _ARTICLE_CILT_SAYI.search(_fold(text)):
        return True
    return False

def _kasif_safe_query(title: str) -> str:
    """
    Prepare a title for inclusion in a KAŞİF ``Ara=`` query.

    KAŞİF treats ``:`` as a field-separator operator: passing
    ``Makam: Türk Sanat Musikisinde Makam Uygulaması`` produces the
    query ``Makam%3A%20Türk%20...``, which returns zero hits even when
    the book is in the catalog. Replacing the colon with a space and
    collapsing whitespace produces a plain keyword query that KAŞİF
    handles correctly.

    Quoting is deliberately not applied: KAŞİF's search is already
    keyword-based, and enclosing quotes in the query string tend to
    reduce matches rather than narrow them.
    """
    cleaned = title.replace(":", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def primary_search_url(reference: Reference) -> str | None:
    """
    Return the best search URL for an unverified reference, or None
    if there is nothing to search for.

    Routing (first match wins):
      - article       -> Google Scholar, query pre-filled and quoted
      - Turkish book  -> KAŞİF, query pre-filled and quoted
      - otherwise     -> Google Scholar, query pre-filled and quoted

    Theses are not special-cased. YÖK Ulusal Tez Merkezi holds only
    theses defended at Turkish universities, so foreign dissertations
    would be sent to a catalog that cannot contain them. Scholar is
    the safer default for thesis references of any origin.
    """
    title = reference.title or reference.raw_text
    if not title:
        return None

    # KAŞİF works better without enclosing quotes; Scholar uses them
    # as an exact-phrase operator and keeps them.
    encoded_quoted = quote(f'"{title}"')

    if is_article_looking(reference):
        return f"https://scholar.google.com/scholar?q={encoded_quoted}"

    if is_turkish_looking(reference):
        # KAŞİF accepts literal ':' and ',' in the Ara= parameter.
        # Encoded forms (%3A, %2C) are treated as field separators and
        # return no results for titles containing either character.
        # Confirmed on "Kültürel bellek: Eski yüksek kültürlerde yazı,
        # hatırlama ve politik kimlik" and "Makam: Türk Sanat
        # Musikisinde Makam Uygulaması".
        encoded_kasif = quote(title, safe=":,")
        return (
            "https://kasif.mkutup.gov.tr/OpacArama.aspx"
            f"?Ara={encoded_kasif}&DtSrc=0&fld=-1&NvBar=0"
        )

    return f"https://scholar.google.com/scholar?q={encoded_quoted}"


def search_link_label(url: str | None) -> str:
    """
    Return a short, human-readable label for a search URL.

    The YÖK Tez branch is retained for robustness even though no code
    currently produces a YÖK Tez URL: if the routing is ever extended
    to include Turkish-only theses, the label is already correct.
    """
    if not url:
        return "Search"
    if "kasif.mkutup.gov.tr" in url:
        return "Search KAŞİF"
    if "tez.yok.gov.tr" in url:
        return "Search YÖK Tez"
    if "scholar.google.com" in url:
        return "Google Scholar"
    return "Search"