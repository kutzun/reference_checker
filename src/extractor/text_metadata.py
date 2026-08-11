"""
Text-based metadata extraction.

Extracts authors and titles from raw reference strings.
Handles APA, MLA, Chicago, IEEE, and other common formats.
"""

import re
from typing import List, Optional

# ---------------------------------------------------------------------------
# Year detection – matches years in parentheses, brackets, or bare
# ---------------------------------------------------------------------------
_YEAR_RE = re.compile(
    r'(\()?\b((?:19|20)\d{2}[a-z]?)\b(?(1)\)|\.?)',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Normalise author separators (Oxford comma, "and", "&")
# ---------------------------------------------------------------------------
_AND_AMPERSAND_RE = re.compile(r'\s*,?\s*(?:&|and)\s*')


def _find_year(text: str) -> Optional[re.Match]:
    """Return the match object for the first publication year found."""
    return _YEAR_RE.search(text)


def _normalise_initials(raw_initials: str) -> str:
    """Convert a raw initial sequence into a normalised 'X. Y.' form."""
    # Remove any existing dots and whitespace, then split into single letters.
    letters = re.sub(r'[.\s]+', '', raw_initials)
    if not letters:
        return raw_initials
    # Re‑build with dot + space between initials, final dot.
    return " ".join(f"{ch}." for ch in letters)


def _extract_last_first(author_block: str) -> List[str]:
    """
    Extract authors from a block that uses 'Surname, Initials' pattern.
    Handles accented characters, multi‑word surnames, and initials
    both with or without dots (e.g., S.A., S A, S, S. A.).
    """
    # Pattern: surname (up to the comma), then initials (with optional dots)
    last_first_re = re.compile(
        r"""
        (?:^|,\s*)                      # start or preceded by a comma
        (                               # group 1: full surname
            [A-ZÀ-ÖØ-öø-ÿ]              # first letter upper/lower/accented
            [A-Za-zÀ-ÖØ-öø-ÿ'`\- ]*?    # rest of surname (reluctant)
        )
        \s*,\s*                         # mandatory comma separator
        (                               # group 2: raw initials
            (?:[A-Z]\.?\s*)+            # one or more initials, dot optional
            (?:-[A-Z]\.?)?              # optional hyphenated initial
        )
        """,
        re.VERBOSE | re.UNICODE,
    )

    authors = []
    for m in last_first_re.finditer(author_block):
        surname = m.group(1).strip()
        raw_initials = m.group(2).strip()
        initials = _normalise_initials(raw_initials)
        authors.append(f"{surname}, {initials}")
    return authors


def _parse_first_last_token(token: str) -> str:
    """Convert a 'First Last' token into 'Surname, Initials'."""
    parts = token.strip().split()
    if not parts:
        return ""
    has_initials = any(p.endswith(".") for p in parts)
    if has_initials:
        idx = 0
        while idx < len(parts) and parts[idx].endswith("."):
            idx += 1
        initials = parts[:idx]
        surname_parts = parts[idx:]
    else:
        if len(parts) == 1:
            return parts[0]
        *first_names, surname = parts
        initials = [f"{fn[0]}." for fn in first_names]
        surname_parts = [surname]

    surname = " ".join(surname_parts)
    initials_str = " ".join(initials)
    return f"{surname}, {initials_str}" if initials_str else surname


def _extract_first_last(text: str) -> List[str]:
    """
    Fallback parser for 'First Last' order (IEEE, some publisher styles).
    Tries to isolate the author block before a quoted title, or before the year.
    """
    quoted_title_re = re.compile(r'"[^"]*"')
    title_match = quoted_title_re.search(text)
    if title_match:
        author_block = text[: title_match.start()].strip()
    else:
        year_match = _find_year(text)
        if year_match:
            author_block = text[: year_match.start()].strip()
        else:
            author_block = text.strip()

    # Remove trailing full stop that often ends the author list.
    author_block = re.sub(r"\s*\.\s*$", "", author_block)
    author_block = _AND_AMPERSAND_RE.sub(", ", author_block)

    tokens = [t.strip() for t in author_block.split(",") if t.strip()]
    authors = [_parse_first_last_token(t) for t in tokens]
    return [a for a in authors if a]


def extract_authors(text: str) -> list[str]:
    year_match = _find_year(text)
    if year_match is None:
        return []                  # no year → cannot reliably isolate author block

    author_part = text[: year_match.start()].strip()
    if not author_part:
        return []

    # Normalise “and” / “&” to a simple comma – early, so the regex sees a
    # uniform list.
    author_part = _AND_AMPERSAND_RE.sub(", ", author_part)

    # Remove **only** a trailing comma or whitespace; DO NOT strip dots that
    # might be part of an initial.
    author_part = author_part.rstrip(", \t")

    # Primary: try “Last, First” extraction.
    authors = _extract_last_first(author_part)

    # Fallback: if nothing was extracted, try “First Last” parser.
    if not authors:
        authors = _extract_first_last(text)

    return authors


def extract_title(text: str) -> str | None:
    """
    Extract title after publication year.
    """
    match = re.search(
        r"\(\d{4}[a-z]?\)\.\s*(.+?)\.(?=\s+[A-Z])",
        text,
    )
    if match is None:
        return None
    title = match.group(1).strip()
    return title or None