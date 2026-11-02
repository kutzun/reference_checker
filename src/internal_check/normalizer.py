"""
Normalization helpers for internal citation checks.

Reduces author names and years to comparable string keys. This module
is deliberately dependency-free so it can be tested in isolation.

Turkish-aware folding is applied unconditionally. It is a no-op for
non-Turkish text and it improves cross-source matching for Turkish
manuscripts, whose names often appear in ASCII form in Crossref and
OpenLibrary responses.
"""

import re
import unicodedata


# ---------------------------------------------------------------------------
# Turkish dotted/dotless I handling
# ---------------------------------------------------------------------------
#
# Turkish has four distinct I letters:
#     I (U+0049)  uppercase dotless
#     ı (U+0131)  lowercase dotless
#     İ (U+0130)  uppercase dotted
#     i (U+0069)  lowercase dotted
#
# Python's casefold() maps I -> i and leaves ı unchanged, which is wrong
# for Turkish. Crossref and OpenLibrary frequently return Turkish names
# in ASCII, so "Yılmaz" in a manuscript arrives as "Yilmaz" from an
# external source. We fold both ı and İ to i before casefolding, which
# makes those two reduce to the same key.
_TURKISH_FOLD = str.maketrans({
    "ı": "i",  # dotless lowercase -> dotted lowercase
    "İ": "i",  # dotted uppercase  -> dotted lowercase
})

# Author name suffixes that should be stripped before comparison.
# Matched only when they appear as a whole word at the end of the
# surname, so "Van Dyke" and "Henry" are not affected. Roman numerals
# are limited to those commonly used as suffixes; "XIV" and higher are
# rare enough that we do not risk the false positives.
_AUTHOR_SUFFIX_RE = re.compile(
    r"\s+(jr|sr|ii|iii|iv|v|2nd|3rd|4th)$"
)


def _fold_case(text: str) -> str:
    """
    Turkish-aware casefolding.

    Maps ı and İ to i before applying str.casefold(). No-op for text
    that does not contain those two characters.
    """
    return text.translate(_TURKISH_FOLD).casefold()


def _strip_diacritics(text: str) -> str:
    """
    Remove combining diacritical marks.

    Examples:
        ``"é"`` -> ``"e"``
        ``"ü"`` -> ``"u"``
        ``"ç"`` -> ``"c"``
        ``"ğ"`` -> ``"g"``
        ``"ş"`` -> ``"s"``

    Note: Turkish ``ı`` does not decompose, so it is handled separately
    by :func:`_fold_case`.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(
        ch for ch in decomposed if not unicodedata.combining(ch)
    )


def normalize_author_name(name: str) -> str:
    """
    Reduce a single author name to a lowercase, punctuation-free key.

    If the name contains a comma, only the part before the first comma
    is kept. This assumes the common ``"Surname, Initials"`` format.

    Examples:
        ``"Smith, J."``                -> ``"smith"``
        ``"Smith, John"``              -> ``"smith john"``
        ``"van der Berg, P."``         -> ``"van der berg"``
        ``"Müller, H."``               -> ``"muller"``
        ``"Yılmaz, A."``               -> ``"yilmaz"``
        ``"Yilmaz, A."``               -> ``"yilmaz"``
        ``"Kılıç, M."``                -> ``"kilic"``
        ``"İstanbul University"``      -> ``"istanbul university"``
        ``"World Health Organization"``-> ``"world health organization"``
    """
    if not name:
        return ""

    name = _strip_diacritics(name)

    if "," in name:
        name = name.split(",", 1)[0]

    name = _fold_case(name)
    name = re.sub(r"[^\w\s]", " ", name, flags=re.UNICODE)
    name = re.sub(r"\s+", " ", name).strip()
    name = _AUTHOR_SUFFIX_RE.sub("", name).strip()
    # Strip trailing single-letter initials. Turkish in-text style
    # writes "Anadol R." where the reference list writes "Anadol, R.";
    # without this step the two normalize to "anadol r" and "anadol"
    # and never match.
    name = re.sub(r"(\s+[a-z])+$", "", name).strip()
    return name


def normalize_year(
    year: int | str | None,
    suffix: str | None = None,
) -> str:
    """
    Produce a normalized year key.

    Examples:
        ``normalize_year(2020)``         -> ``"2020"``
        ``normalize_year(2020, "a")``    -> ``"2020a"``
        ``normalize_year("2020", "A")``  -> ``"2020a"``
        ``normalize_year(None)``         -> ``""``
    """
    if year is None:
        return ""

    year_str = str(year).strip()
    if not year_str:
        return ""

    if suffix:
        suffix = suffix.strip().lower()
        return f"{year_str}{suffix}"

    return year_str


def first_author_key(authors: list[str]) -> str:
    """
    Return the normalized key of the first author, or an empty string
    if the list is empty.
    """
    if not authors:
        return ""
    return normalize_author_name(authors[0])


def citation_key(
    first_author: str,
    year: int | str | None,
    suffix: str | None = None,
) -> str:
    """
    Produce a canonical matching key for a citation.

    The key is ``"<author>:<year>"``, or an empty string if either
    component is missing.

    Examples:
        ``citation_key("Smith", 2020)``         -> ``"smith:2020"``
        ``citation_key("Smith", 2020, "a")``    -> ``"smith:2020a"``
        ``citation_key("Yılmaz", 2020)``        -> ``"yilmaz:2020"``
        ``citation_key("Yilmaz", 2020)``        -> ``"yilmaz:2020"``
        ``citation_key("", 2020)``              -> ``""``
    """
    author_key = normalize_author_name(first_author)
    year_key = normalize_year(year, suffix)

    if not author_key or not year_key:
        return ""

    return f"{author_key}:{year_key}"