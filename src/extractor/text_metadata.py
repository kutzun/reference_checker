"""
Text-based metadata extraction.

Extracts authors and titles from raw reference strings.
Handles APA, MLA, Chicago, IEEE, and many Turkish/Ottoman styles.
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
_AND_AMPERSAND_RE = re.compile(r'\s*,?\s*(?:\band\b|&)\s*')

# Words that indicate a token is NOT an author name (editor, volume, etc.)
_NON_AUTHOR_TOKENS = {
    'haz.', 'haz', 'çev.', 'çev', 'ed.', 'trans.',
    'cilt', 'sayı', 's.', 'pp.', 'no', 'vol', 'p', 'pp',
}


def _find_year(text: str) -> Optional[re.Match]:
    """Return the match object for the first publication year found."""
    return _YEAR_RE.search(text)


def _normalise_initials(raw_initials: str) -> str:
    """Convert a raw initial sequence into a normalised 'X. Y.' form."""
    letters = re.sub(r'[.\s]+', '', raw_initials)
    if not letters:
        return raw_initials
    return " ".join(f"{ch}." for ch in letters)


def _is_likely_non_author(token: str) -> bool:
    """Return True if *token* looks like an editor/translator note or volume/page info."""
    token = token.strip().rstrip(".,;:")
    if not token:
        return True
    if re.fullmatch(r'[a-zA-Z]', token):
        return True
    return token.lower() in _NON_AUTHOR_TOKENS


def _extract_last_first(author_block: str) -> List[str]:
    """
    Extract authors from a block that uses 'Surname, Initials' pattern.
    Handles accented characters, multi‑word surnames, and initials
    both with or without dots (e.g., S.A., S A, S, S. A.).
    """
    last_first_re = re.compile(
        r"""
        (?:^|,\s*)                      # start or preceded by a comma
        (                               # group 1: full surname
            (?:                         # optional lowercase particles
                [a-zà-öø-ÿ]             # particle starts lowercase
                [A-Za-zÀ-ÖØ-öø-ÿ'`\-]*  # rest of particle (no spaces)
                \s+
            )*
            [A-ZÀ-ÖØ-öø-ÿ]              # main surname first letter
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
    token = token.strip().rstrip(".,;:")
    token = token.strip()
    if not token:
        return ""
    parts = token.split()
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
    if not surname:
        return ""
    initials_str = " ".join(initials)
    return f"{surname}, {initials_str}" if initials_str else surname


def _extract_first_last(text: str) -> List[str]:
    """Fallback parser for 'First Last' order (IEEE, some publisher styles)."""
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
    authors = []
    for t in tokens:
        if re.fullmatch(r"[,\s\.\-]+", t):
            continue
        if _is_likely_non_author(t):
            continue
        parsed = _parse_first_last_token(t)
        if parsed:
            authors.append(parsed)
    return authors


def extract_authors(text: str) -> list[str]:
    """
    Extract authors from a bibliographic reference string.

    Supports APA, MLA, Chicago, IEEE, and common publisher formats.
    Returns a list of authors in ``Surname, X. Y.`` format (initials
    always dotted and space‑separated).
    """
    year_match = _find_year(text)
    if year_match is None:
        return []

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

    # If any extracted author contains more than one comma, the regex likely
    # matched garbage.  Discard and fall back to the first‑last parser.
    if authors and any(a.count(',') > 1 for a in authors):
        authors = []

    # Fallback: if nothing was extracted, try “First Last” parser.
    if not authors:
        authors = _extract_first_last(text)

    # Final cleanup: remove entries that are clearly not author names
    authors = [a for a in authors if not _is_likely_non_author(a)]
    return authors


def extract_title(text: str) -> str | None:
    """
    Extract title after publication year.

    Supports:
    - (year). Title. ...
    - (year, ...). Title. ...
    - bare year. Title. ...
    - Journal articles with quoted title (e.g., "Title")
    - Turkish/Ottoman style: title often appears between author and editor/publisher,
      before the year.
    """
    # --- Pattern 1: quoted title (highest precision) -------------------------
    quoted = re.search(r'"([^"]+)"', text)
    if quoted:
        return quoted.group(1).strip()

    # --- Pattern 2: (year). Title. ------------------------------------------
    match = re.search(r"\(\d{4}[a-z]?\)\.\s*(.+?)\.(?=\s+[A-Z])", text)
    if match:
        title = match.group(1).strip()
        if not _is_likely_page_fragment(title):
            return _clean_title(title)

    # --- Pattern 3: (year, ...). Title. ------------------------------------
    match = re.search(r"\(\d{4}[a-z]?,\s*[^)]+\)\.\s*(.+?)\.(?=\s+[A-Z])", text)
    if match:
        title = match.group(1).strip()
        if not _is_likely_page_fragment(title):
            return _clean_title(title)

    # --- Pattern 4: year). Title. (opening parenthesis maybe missing) -------
    match = re.search(r"\(\d{4}[a-z]?\)\s*\.\s*(.+?)\.(?=\s+[A-Z])", text)
    if match:
        title = match.group(1).strip()
        if not _is_likely_page_fragment(title):
            return _clean_title(title)

    # --- Pattern 5: bare year. Title. ---------------------------------------
    match = re.search(r"\b(?:19|20)\d{2}[a-z]?\.\s*(.+?)\.(?=\s+[A-Z])", text)
    if match:
        title = match.group(1).strip()
        if not _is_likely_page_fragment(title):
            return _clean_title(title)

    # --- Pattern 6: catch-all after year, rejecting obvious page fragments -
    # Accepts both "YEAR. Title." and "(YEAR). Title." forms when the title
    # is the last fragment in the string.
    match = re.search(r"\b(?:19|20)\d{2}[a-z]?\b\)?[.,;]?\s*(.+?)\.(?=\s|$)", text)
    if match:
        title = match.group(1).strip()
        if not _is_likely_page_fragment(title):
            return _clean_title(title)

    # --- Final fallback: search the text before the year for a plausible title --
    year_match = _find_year(text)
    if year_match:
        pre_year = text[: year_match.start()].strip()
        # Split by commas, keep segments that don't look like authors/editors
        parts = [p.strip() for p in pre_year.split(",") if p.strip()]
        candidates = []
        for part in parts:
            if _is_likely_non_author(part):
                continue
            if _is_likely_publisher_or_translator(part):
                continue
            if len(part.split()) >= 2:
                candidates.append(part)
        if candidates:
            best_candidate = max(candidates, key=len)
            # If the best candidate is actually a publisher or translator note,
            # it's better to return None so the caller falls back to raw_text.
            if not _is_likely_publisher_or_translator(best_candidate):
                return _clean_title(best_candidate)
            # else fall through and return None

    return None


def _is_likely_page_fragment(text: str) -> bool:
    """Return True if *text* looks like a page number or volume/issue info."""
    text = text.strip().rstrip(".,;")
    if not text:
        return True
    if re.fullmatch(r'[a-zA-Z]', text):
        return True
    if re.fullmatch(r'[sp]\.?\s*\d+(\-\d+)?', text):
        return True
    if re.fullmatch(r'\d+(\-\d+)?', text):
        return True
    if re.match(r'(Cilt|Sayı|Vol|No|Issue)\s*\d+', text, re.IGNORECASE):
        return True
    return False


def _is_likely_publisher_or_translator(text: str) -> bool:
    """Return True if *text* looks like a publisher name or translator note."""
    text_lower = text.strip().lower()
    # Turkish publisher indicators
    pub_words = [
        'yayınları', 'yayıncılık', 'yayınevi', 'basımevi', 'kitabevi',
        'üniversitesi', 'kurumu', 'kurum', 'matbaası', 'basım'
    ]
    if any(word in text_lower for word in pub_words):
        return True
    # English publisher indicators
    if any(word in text_lower for word in ['press', 'publishing']):
        return True
    # Translator / editor markers (anywhere in the text, not just at the start)
    if any(marker in text_lower for marker in ['çev.', 'haz.', 'ed.', 'trans.']):
        return True
    return False


def _clean_title(title: str) -> str | None:
    """Remove leading stray punctuation like ')' that may have been captured.

    Returns ``None`` if nothing meaningful remains, so callers can fall
    through to their own ``None`` return instead of handing back ``""``.
    """
    title = title.strip()
    if title.startswith(')'):
        title = title[1:].strip()
    return title or None
