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

# Markers that identify web/report references with an access date.
# Used to gate venue-stripping, which only applies to web-style entries.
_ACCESS_MARKER_RE = re.compile(
    r"retrieved|accessed date|erişim",
    re.IGNORECASE,
)

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
    Extract authors from a block that uses the 'Surname, Initials'
    pattern. Handles accented characters including Turkish letters in
    Latin Extended-A (ı, İ, ğ, Ğ, ş, Ş), multi-word surnames with
    lowercase particles, and initials with or without dots.

    The trailing negative lookahead rejects a 'surname' that is
    actually a given name: ``"Kılıç, Mahmud Erol, ..."`` produces no
    match here because after the alleged initial ``M`` the next
    character is a lowercase letter, meaning ``Mahmud`` is a full
    given name, not initials. The caller's fallback then extracts
    ``Kılıç`` correctly. For ``"Smith, J., Brown, A."`` the initial
    ``J`` is followed by a period, so the pattern matches as before.
    """
    last_first_re = re.compile(
        r"""
        (?:^|,\s*)                      # start or preceded by a comma
        (                               # group 1: full surname
            (?:                         # optional lowercase particles
                [a-zà-öø-ÿā-ſ]
                [A-Za-zÀ-ÖØ-öø-ÿĀ-ſ'`\-]*
                \s+
            )*
            [A-ZÀ-ÖØ-öø-ÿĀ-ſ]           # main surname first letter
            [A-Za-zÀ-ÖØ-öø-ÿĀ-ſ'`\- ]*? # rest of surname (reluctant)
        )
        \s*,\s*                         # mandatory comma separator
        (                               # group 2: raw initials
            (?:[A-ZÀ-ÖØ-ÞĀ-ſ]\.?\s*)+   # one or more initials
            (?:-[A-ZÀ-ÖØ-ÞĀ-ſ]\.?)?     # optional hyphenated initial
        )
        (?![A-Za-zÀ-ÖØ-öø-ÿĀ-ſ])        # next char must not be a letter
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
    # Compound surnames with an internal hyphen or apostrophe
    # (Turkish/Ottoman style, e.g. "Ahmed-i Dâ'î", "Şeyh Galib",
    # "Koca Ragıp Paşa") are already in the form the caller wants.
    # Splitting on whitespace would pick the last word as the
    # surname and misattribute the reference.
    if "-" in token or "'" in token or "\u2019" in token:
        return token
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

    Single-name institutional authors ("Türk Dil Kurumu", "IATA",
    "Euronews") are returned as-is. Reference styles always separate
    personal surnames from initials with a comma, so absence of a
    comma means the block is a single institutional name.
    """
    year_match = _find_year(text)
    if year_match is None:
        return []

    author_part = text[: year_match.start()].strip()
    if not author_part:
        return []

    # Trailing comma/space is common when the raw text reads "IATA, (2024),".
    author_part = author_part.rstrip(", \t")

    # Institutional author: no comma means the block cannot be a
    # "Surname, Initials" list. Strip any leftover opening bracket that
    # a year-in-parens regex may have left behind ("Euronews. (").
    if "," not in author_part:
        institutional = author_part.rstrip(". ([{")
        if institutional:
            return [institutional]

    # Normalise "and" / "&" to a simple comma so the regex below sees a
    # uniform list.
    author_part = _AND_AMPERSAND_RE.sub(", ", author_part)

    # Primary: try "Last, First" extraction.
    authors = _extract_last_first(author_part)

    # If any extracted author contains more than one comma, the regex
    # likely matched garbage. Discard and fall back to the first-last parser.
    if authors and any(a.count(',') > 1 for a in authors):
        authors = []

    # Fallback: if nothing was extracted, try "First Last" parser.
    if not authors:
        authors = _extract_first_last(text)

    # Final cleanup: remove entries that are clearly not author names.
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
    # --- Pattern 1: fully-quoted title (highest precision) -------------------
    # Only fires when the TITLE itself is quoted, i.e. the opening quote
    # appears immediately after the year block. An embedded quote inside
    # an unquoted title ("Facebook wants to move to "the metaverse" — ...")
    # must NOT trigger this; those fall through to the patterns below.
    quoted = re.search(
        r'(?:\(\d{4}[a-z]?\)|\b\d{4}[a-z]?)[.,]\s*"([^"]+)"',
        text,
    )
    if quoted:
        return quoted.group(1).strip()

    # --- Pattern 1b: URL-tail web/report entries -----------------------------
    # Handles references where the title runs directly up to a URL:
    #   (YEAR), Title, https://...
    #   (YEAR, Month Day). Title. https://...
    # Anchored on the URL, so it cannot swallow later fields.
    url_tail = re.search(
        r"\(\d{4}[a-z]?(?:,\s*[^)]*)?\)[.,]\s*([^?.]+?)[.,]?\s*https?://",
        text,
    )
    if url_tail:
        candidate = url_tail.group(1).strip()
        cleaned = _clean_title(candidate, text)
        if cleaned and not _is_likely_page_fragment(cleaned):
            return cleaned

    # --- Pattern 2b: (year). Title (Translator/Editor note). ----------------
    # Handles translated/edited works where a parenthetical note sits
    # between the title and the publisher:
    #   Bombaci, A. (1968). Histoire de la littérature turque
    #       (I. Melikoff, Çev.). Librairie C. Klincksieck.
    # Markers: çev. (çeviren), haz. (hazırlayan), ed. (editör),
    #          derl. (derleyen), aktar. (aktaran), trans.
    # A comma is required before the marker, so "(Eds.)" or "(Ed.)"
    # alone do not trigger this pattern.
    translator_note = re.search(
        r"\(\d{4}[a-z]?\)\.\s*(.+?)\s*\([^)]+,\s*"
        r"(?:çev|haz|ed|eds|derl|aktar|trans)\.[^)]*\)",
        text,
        re.IGNORECASE,
    )
    if translator_note:
        candidate = translator_note.group(1).strip()
        if not _is_likely_page_fragment(candidate):
            return _clean_title(candidate, text)

    # --- Pattern 2: (year). Title. ------------------------------------------
    # The (?<![A-Z]) lookbehind prevents an initial like "I." from being
    # treated as the end of the title.
    match = re.search(
        r"\(\d{4}[a-z]?\)\.\s*(.+?)(?<![A-Z])\.(?=\s+[A-Z])",
        text,
    )
    if match:
        title = match.group(1).strip()
        if not _is_likely_page_fragment(title):
            return _clean_title(title, text)

    # --- Pattern 3: (year, ...). Title. ------------------------------------
    match = re.search(r"\(\d{4}[a-z]?,\s*[^)]+\)\.\s*(.+?)\.(?=\s+[A-Z])", text)
    if match:
        title = match.group(1).strip()
        if not _is_likely_page_fragment(title):
            return _clean_title(title, text)

    # --- Pattern 4: year). Title. (opening parenthesis maybe missing) -------
    match = re.search(r"\(\d{4}[a-z]?\)\s*\.\s*(.+?)\.(?=\s+[A-Z])", text)
    if match:
        title = match.group(1).strip()
        if not _is_likely_page_fragment(title):
            return _clean_title(title, text)

    # --- Pattern 5: bare year. Title. ---------------------------------------
    match = re.search(r"\b(?:19|20)\d{2}[a-z]?\.\s*(.+?)\.(?=\s+[A-Z])", text)
    if match:
        title = match.group(1).strip()
        if not _is_likely_page_fragment(title):
            return _clean_title(title, text)

    # --- Pattern 6: catch-all after year, rejecting obvious page fragments -
    # Accepts both "YEAR. Title." and "(YEAR). Title." forms when the title
    # is the last fragment in the string.
    match = re.search(r"\b(?:19|20)\d{2}[a-z]?\b\)?[.,;]?\s*(.+?)\.(?=\s|$)", text)
    if match:
        title = match.group(1).strip()
        if not _is_likely_page_fragment(title):
            return _clean_title(title, text)

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
                return _clean_title(best_candidate, text)
            # else fall through and return None

    return None

def extract_journal(text: str) -> str | None:
    """
    Extract journal name from a journal-article reference.

    Journal names sit immediately before a volume/issue marker:

        "... Title. Journal Name, Vol. 13 No. 6, pp. 1312-1333."
        "... Title. Journal Name, 11(4), 467-469."
        "... Title. Journal Name, 1(2), 116-125."

    The candidate is restricted so it cannot contain sentence-ending
    punctuation, which keeps the match from starting inside the title.
    Returns the journal name exactly as it appears in the raw text
    (paste-joins and all), or None if no pattern matched.
    """
    # Pattern A: "Journal Name, Vol. N" (Harvard-style volume marker)
    m = re.search(r"([^,.!?;:]+?),\s*Vol\.\s*\d+", text)
    if m:
        candidate = m.group(1).strip().lstrip('"?,;:').strip()
        if candidate:
            return candidate

    # Pattern B: "Journal Name, N(M)" (APA-style volume(issue) marker)
    m = re.search(r"([^,.!?;:]+?),\s*\d+\s*\(\s*\d+\s*\)", text)
    if m:
        candidate = m.group(1).strip().lstrip('"?,;:').strip()
        if candidate:
            return candidate

    # Pattern C: "Journal Name, N, N-N" — comma-separated Harvard-ish
    # style with no Vol./No. markers and no parentheses. Anchored on
    # the period that ends the title, so the journal name starts with
    # a capital letter after a sentence boundary.
    m = re.search(
        r"\.\s+([A-ZÇĞİÖŞÜ][^.!?;:]*?),\s*\d+,\s*\d+\s*[-–]\s*\d+",
        text,
    )
    if m:
        candidate = m.group(1).strip()
        if candidate:
            return candidate

    return None

def extract_volume(text: str) -> str | None:
    """
    Extract journal volume from a journal-article reference.

    Supports the two markers our journal names appear with:

        "Journal Name, Vol. 13 No. 6, ..."  -> "13"  (Harvard)
        "Journal Name, 11(4), 467-469."     -> "11"  (APA)

    Returns the volume as a string, or None if no pattern matched.
    """
    # Harvard-style: "Vol. 13" or "Vol. 13A"
    m = re.search(r"\bVol\.\s*(\d+[A-Za-z]?)", text)
    if m:
        return m.group(1)

    # APA-style: ", 11(4)" — comma, volume, open paren, issue.
    m = re.search(r",\s*(\d+[A-Za-z]?)\s*\(\s*\d+\s*\)", text)
    if m:
        return m.group(1)

    # Comma-separated style: ", 37, 189-218" — journal, volume, pages.
    # The volume is the number between the journal name and the page range.
    m = re.search(
        r",\s*(\d+[A-Za-z]?)\s*,\s*\d+\s*[-–]\s*\d+",
        text,
    )
    if m:
        return m.group(1)

    return None

def extract_issue(text: str) -> str | None:
    """
    Extract journal issue from a journal-article reference.

    Supports the two markers our volumes appear with:

        "Journal Name, Vol. 13 No. 6, ..."  -> "6"  (Harvard)
        "Journal Name, 11(4), 467-469."     -> "4"  (APA)

    Returns the issue as a string, or None if no pattern matched.
    """
    # Harvard-style: "No. 6" or "No. 6A"
    m = re.search(r"\bNo\.\s*(\d+[A-Za-z]?)", text)
    if m:
        return m.group(1)

    # APA-style: ", 11(4)" — comma, volume, open paren, issue.
    m = re.search(r",\s*\d+[A-Za-z]?\s*\(\s*(\d+[A-Za-z]?)\s*\)", text)
    if m:
        return m.group(1)

    return None

def extract_pages(text: str) -> str | None:
    """
    Extract page range from a journal-article reference.

    Supports the markers used across our fixtures:

        "... Vol. 13 No. 6, pp. 1312-1333."      -> "1312-1333"
        "... 11(4), 467-469."                    -> "467-469"
        "... 1(2), 116–125."                     -> "116–125"

    Preserves the dash character as it appears in the raw text
    (hyphen, en-dash). Returns None if no range matched.
    """
    # Pattern A: "pp. NNN-NNN" (Harvard and book-chapter styles)
    m = re.search(r"\bpp\.\s*(\d+\s*[-–]\s*\d+)", text)
    if m:
        return m.group(1).replace(" ", "")

    # Pattern B: ", NNN-NNN" following a "volume(issue)," marker (APA)
    m = re.search(
        r"\d+[A-Za-z]?\s*\(\s*\d+\s*\)\s*,\s*(\d+\s*[-–]\s*\d+)",
        text,
    )
    if m:
        return m.group(1).replace(" ", "")

    # Pattern C: ", N, NNN-NNN" — comma-separated style with no parens.
    m = re.search(
        r",\s*\d+[A-Za-z]?\s*,\s*(\d+\s*[-–]\s*\d+)",
        text,
    )
    if m:
        return m.group(1).replace(" ", "")

    return None

def extract_publisher(text: str) -> str | None:
    """
    Extract publisher from book, book-chapter, and report references.

    Publisher names have no universal delimiter, so this function uses
    three separate anchors, tried in order, each targeted at a specific
    reference shape:

    A. Turkish publishers ending in a known marker (Yayınları,
       Yayınevi, Yayıncılık, Basımevi, Kitabevi, Matbaası), at the
       start of a sentence:
           "... (2. baskı). Türkiye Felsefe KurumuYayınları."

    B. Western publishers following a page range and preceding a URL:
           "... (pp. 28-53). IGI Global. https://doi.org/..."

    C. Translated-book publishers, at the end of the string, after a
       translator note in parentheses:
           "... (I. Melikoff, Çev.).Librairie C. Klincksieck."

    Returns the publisher name as a string, or None if no anchor matched.
    """
    # A. Turkish publishers ending in a known marker.
    turkish_marker = (
        r"(?:Yayınları|Yayınevi|Yayıncılık|Basımevi|Kitabevi|Matbaası)"
    )
    m = re.search(
        r"(?<=\. )([A-ZÇĞİÖŞÜ][^.;:]*?" + turkish_marker + r")\.",
        text,
    )
    if m:
        return m.group(1).strip()

    # B. Western publishers after a page range, followed by a URL.
    m = re.search(
        r"\(pp\.\s*\d+\s*[-–]\s*\d+\)\.\s*"
        r"([A-Z][^.;:]*?\s+[^.;:]+?)\.(?=\s+https?://)",
        text,
    )
    if m:
        return m.group(1).strip()

    # C. Translated-book publishers at the end of the string.
    m = re.search(
        r"\([^)]*,\s*(?:Çev|Çeviren|Trans)\.?\)\.\s*"
        r"([A-Z][^;:]+)\.\s*$",
        text,
    )
    if m:
        return m.group(1).strip()

    # D. Western publishers ending in a known English marker, at the end
    #    of the string. Covers "Cambridge University Press", "... Publishing",
    #    "... Publishers", "... Books", "... Publications".
    m = re.search(
        r"([A-Z][^.;:]*(?:Press|Publishing|Publishers|Books|Publications))"
        r"\.\s*$",
        text,
    )
    if m:
        return m.group(1).strip()

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


def _clean_title(title: str, text: str = "") -> str | None:
    """Remove leading stray punctuation and trailing annotations.

    Returns ``None`` if nothing meaningful remains, so callers can fall
    through to their own ``None`` return instead of handing back ``""``.

    ``text`` is the full raw reference. When it contains an access
    marker (Retrieved / Erişim Tarihi / Accessed Date), we treat the
    title as a web-style title and additionally strip a trailing venue
    name that a paste-join glued to the title (e.g. ``...worried.Toronto
    Star`` or ``...yapacak? DW Türkçe``).
    """
    title = title.strip()
    if title.startswith(')'):
        title = title[1:].strip()
    # Strip trailing bracketed annotations: [Video], [PDF],
    # [Yüksek lisans tezi, ...], [Conference presentation].
    title = re.sub(r"\s*\[[^\]]*\]\s*$", "", title)
    # Strip trailing parenthetical suffixes: (2. baskı), (1. baskı).
    title = re.sub(r"\s*\([^)]*\)\s*$", "", title)
    title = title.strip()

    # Strip a trailing venue name (web/report entries only).
    if text and _ACCESS_MARKER_RE.search(text):
        m = re.search(r"[.?!](?=[\s]*[A-ZÇĞİÖŞÜ])", title)
        if m:
            head = title[: m.start()].rstrip()
            tail = title[m.end():].lstrip()
            head_last_word = head.split()[-1] if head.split() else ""
            # Conservative: preceding word must be ≥ 3 chars (excludes
            # abbreviations like "et al.", "Dr.", "St.") and the tail
            # must be short (1–4 words).
            if len(head_last_word) >= 3 and 1 <= len(tail.split()) <= 4:
                if title[m.start()] in "?!":
                    head = head + title[m.start()]
                title = head

    return title or None
