"""
Reference entry splitting.

Separates a reference section into individual reference entries.

Real manuscripts often break a single reference across two or more
paragraphs (a citation line followed by a URL, a shelf-mark, or an
access date). This module joins such continuation lines back onto the
entry they belong to before applying the reference filter.
"""

import re


# Publication year, allowing pre-1900 for historical sources.
_YEAR_RE = re.compile(r"\b(?:1[0-9]{3}|20\d{2})\b")

# "No date yet" markers in English and Turkish.
_NO_YEAR_RE = re.compile(
    r"\b(?:in\s+press|forthcoming|t\.\s*y\.?|n\.\s*d\.?|n\.\s*y\.?)\b",
    re.IGNORECASE,
)

# Academic context markers that justify an entry even without a year.
_ACADEMIC_RE = re.compile(
    r"\b(?:doctoral\s+dissertation|ph\.?\s*d\.?|master'?s\s+thesis|"
    r"yüksek\s+lisans\s+tezi|doktora\s+tezi|tezi)\b",
    re.IGNORECASE,
)

# Page range such as "301-316" or "215-277".
_PAGE_RANGE_RE = re.compile(r"\b\d{1,4}\s*[-–]\s*\d{1,4}\b")

# A line that continues the previous entry. Either it starts with a URL,
# or it is a single token (no whitespace) beginning with a lowercase
# letter or digit (shelf-marks like "bsb10527978_00179_u001").
_CONTINUATION_RE = re.compile(
    r"^\s*(?:https?://|[a-z0-9]\S*$)",
    re.IGNORECASE,
)

# Lines that start with a section heading and are never references.
_HEADING_RE = re.compile(
    r"^\s*(?:Figure|Table|Appendix|Source\s+data)\b",
    re.IGNORECASE,
)


def split_references(
    paragraphs: list[str],
) -> list[str]:
    """
    Split reference section paragraphs into individual entries.

    Continuation paragraphs (URLs, shelf-marks, access dates) are first
    joined back onto the entry they continue. The joined entries are
    then filtered to keep only those that look like real references.
    """
    joined = _join_continuations(paragraphs)

    return [entry for entry in joined if _is_likely_reference(entry)]


def _join_continuations(paragraphs: list[str]) -> list[str]:
    """Join continuation paragraphs onto the previous entry."""
    joined: list[str] = []

    for paragraph in paragraphs:
        cleaned = clean_reference(paragraph)
        if not cleaned:
            continue

        if joined and _is_continuation(cleaned):
            joined[-1] = f"{joined[-1]} {cleaned}"
        else:
            joined.append(cleaned)

    return joined


def _is_continuation(text: str) -> bool:
    """
    Return True if *text* continues the previous entry.

    Two shapes are treated as continuations:

    - A URL ("http://..." or "https://...").
    - A single-token line with no whitespace, starting with a lowercase
      letter or digit (shelf-marks, DOI fragments, accession codes).
    """
    return bool(_CONTINUATION_RE.match(text))


def clean_reference(
    text: str,
) -> str:
    """
    Clean a single reference entry.

    Removes leading/trailing whitespace and collapses runs of
    whitespace (including non-breaking spaces from DOCX) to single
    regular spaces.
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _is_likely_reference(text: str) -> bool:
    """
    Return True if *text* looks like a bibliographic reference.

    An entry qualifies if it is at least 20 characters long and meets
    any of:

    - Contains a four-digit year (1000-2099).
    - Contains a "no date yet" marker (in press, forthcoming, t.y., n.d.).
    - Contains an academic context marker (dissertation, thesis, tezi).
    - Contains a page range and at least five words.
    """
    if len(text) < 20:
        return False

    if _HEADING_RE.match(text):
        return False

    if _YEAR_RE.search(text):
        return True

    if _NO_YEAR_RE.search(text):
        return True

    if _ACADEMIC_RE.search(text):
        return True

    if _PAGE_RANGE_RE.search(text) and len(text.split()) >= 5:
        return True

    return False