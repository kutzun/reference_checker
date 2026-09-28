"""
Pick the best search engine for a reference that failed verification.

Different reference types benefit from different search engines:

- Turkish theses are best found on YÖK Ulusal Tez Merkezi, which holds
  every thesis defended at a Turkish university. Google Scholar's
  coverage of Turkish theses is incomplete because many institutional
  repositories do not expose standard, harvestable metadata.
- Other Turkish-language references (books, articles, chapters) are
  best found on Milli Kütüphane's KAŞİF catalog, which holds every
  book published in Turkey since 1934.
- Everything else goes to Google Scholar, which indexes the widest
  range of international academic material.

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

# Structural markers that reliably indicate a Turkish-language citation.
_TURKISH_MARKERS = re.compile(
    r"\byayinlari\b|\byayinevi\b|\bbasimevi\b|\bkitabevi\b|\bdergisi\b"
    r"|\bcilt\b|\bsayi\b|\bcev\b|\bhaz\b"
)

# Markers that indicate a thesis rather than a book or article.
# `tez` is matched with a small set of common Turkish suffixes only,
# so that a surname like `Tezcan` does not falsely trigger.
_THESIS_MARKERS = re.compile(
    r"\btez(i|in|ler|lerin|e|de|den)?\b"
    r"|yuksek lisans|doktora|sanatta yeterlik|tipta uzmanlik"
    r"|enstitu|danisman"
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


def is_turkish_looking(reference: Reference) -> bool:
    """True if the reference looks like it is written in Turkish."""
    text = _reference_text(reference)
    if not text:
        return False
    if any(c in _TURKISH_CHARS for c in text):
        return True
    return bool(_TURKISH_MARKERS.search(_fold(text)))


def is_thesis_looking(reference: Reference) -> bool:
    """True if the reference looks like a thesis (any language)."""
    text = _reference_text(reference)
    if not text:
        return False
    return bool(_THESIS_MARKERS.search(_fold(text)))


def primary_search_url(reference: Reference) -> str | None:
    """
    Return the best search URL for an unverified reference, or None
    if there is nothing to search for.

    Routing:
      - thesis        -> YÖK Tez search page (no query pre-fill
                         possible; the site uses POST, not GET)
      - Turkish       -> KAŞİF, query pre-filled and quoted
      - otherwise     -> Google Scholar, query pre-filled and quoted
    """
    if is_thesis_looking(reference):
        return "https://tez.yok.gov.tr/UlusalTezMerkezi/tarama.jsp"

    title = reference.title or reference.raw_text
    if not title:
        return None

    encoded = quote(f'"{title}"')

    if is_turkish_looking(reference):
        return (
            "https://kasif.mkutup.gov.tr/OpacArama.aspx"
            f"?Ara={encoded}&DtSrc=0&fld=-1&NvBar=0"
        )

    return f"https://scholar.google.com/scholar?q={encoded}"

def search_link_label(url: str | None) -> str:
    """
    Return a short, human-readable label for a search URL.

    Used by the GUI and the HTML exporter so that users see the actual
    destination ("Search KAŞİF", "Search YÖK Tez", "Google Scholar")
    instead of a generic "Google Search" that is often wrong.
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