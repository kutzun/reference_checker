"""
Text-based metadata extraction.

Extracts authors and titles from raw reference strings.
Handles APA, MLA, Chicago, IEEE, and many Turkish/Ottoman styles.

Known limitation
----------------
Multi-author Turkish references that use "ve" as the separator between
two complete "Surname, Given" pairs (e.g.:

    Öztürk, Okan Murat, Beşiroğlu, Şehvar Şahin ve Bayraktarkatal,
    Mehmet Emin, "Makamı Anlamak: ...", Porte Akademik Müzik ve Dans
    Araştırmaları Dergisi, Sayı 10, 2014, s. 9-36.

) currently extract only the first author. Adding "ve" as an author
separator would also split on "ve" inside Turkish titles
("Dil ve Tarih-Coğrafya", "Safiyyüddin ... ve Kitabü'l-Edvârı") and
publisher names, so this is deliberately left unhandled. Any fix must
distinguish "ve between two Surname, Given pairs" from "ve inside a
phrase", which requires more context than this module currently has.
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

# Contributor / role notes in parentheses — "(D. Bengi, Röportaj Yapan)",
# "(N. K. Denzin, & Y. S. Lincoln, Dü)", "(T. May, Düzenleyen)".
# Requires an "X." initial prefix followed by a capitalised given name,
# so title-internal parens ("(Perde, Nağme, …)"), edition notes
# ("(5. b.)", "(2. baskı)") and marker-only forms ("(Eds.)",
# "(Yönetmen)") are untouched. Translator/editor notes ("(I. Melikoff,
# Çev.)", "(A. Smith, ed.)") are EXCLUDED via the negative lookahead —
# Pattern 2b in extract_title already handles those, and stripping them
# first regresses the Bombaci shape.
_ROLE_NOTE_RE = re.compile(
    r"\s*\((?=(?:[A-ZÇĞİÖŞÜ]\.\s*)+[A-ZÇĞİÖŞÜ][a-zçğıöşü])"
    r"(?![^)]*(?:çev|haz|ed|eds|derl|aktar|trans)\.[^)]*\))"
    r"[^)]*\)",
    re.IGNORECASE,
)

# No-date placeholders: APA "t.y." (Türkçe) / "n.d." (English).
_NO_DATE_RE = re.compile(r"\(\s*(?:t\.y\.|n\.d\.)\s*\)", re.IGNORECASE)

# Trailing access statements — Turkish "18 Ocak 2026 tarihinde … erişim
# sağlanmıştır" and English "Retrieved …" / "Accessed …". Stripped before
# parsing so the access year is not mistaken for a publication year.
# Deliberately does NOT match "Erişim Tarihi: …", whose marker must
# survive for _clean_title's venue-strip path.
_ACCESS_TAIL_RE = re.compile(
    r"\s+\d{1,2}\s+\S+\s+\d{4}\s+tarihinde.*$"
    r"|\s+Retrieved\s+.*$"
    r"|\s+Accessed\s+.*$",
    re.IGNORECASE | re.DOTALL,
)

# Words that indicate a token is NOT an author name (editor, volume, etc.)
_NON_AUTHOR_TOKENS = {
    'haz.', 'haz', 'çev.', 'çev', 'ed.', 'trans.',
    'cilt', 'sayı', 's.', 'pp.', 'no', 'vol', 'p', 'pp',
}

# Lowercase particles that can appear inside a personal name. Used by
# ``_is_name_segment`` to accept segments like "van der Berg" or
# "İbn Haldun" without accepting title fragments like "and Mysticism"
# or "Dil ve Tarih-Coğrafya".
_NAME_PARTICLES = {
    'de', 'van', 'von', 'della', 'di', 'del', 'bin', 'ibn', 'al', 'el',
    'ter', 'ten', 'der', 'den', 'la', 'le', 'du', 'da',
}

# Institutional authors that appear comma-separated from their title in
# Harvard year-at-end entries:
#     Türk Dil Kurumu, Türkçe Sözlük, Milliyet Yayınları, İstanbul 1992.
# Without this allowlist, ``_parse_first_last_token`` reads
# "Türk Dil Kurumu" as a surname and "Türkçe Sözlük" as a given name,
# producing the phantom author "Türk Dil Kurumu, T. S.".
_INSTITUTIONAL_AUTHOR_RE = re.compile(
    r'^('
    r'Türk\s+Dil\s+Kurumu'
    r'|Türkiye\s+Büyük\s+Millet\s+Meclisi'
    r'|İletişim\s+Başkanlığı'
    r'|Basın\s+İlan\s+Kurumu'
    r'|Resm[îi]\s+Gazete'
    r')$',
    re.UNICODE,
)

# Title-internal connectors — kept as title even when the segment starts
# lowercase ("and Mysticism in the Ottoman Empire" continues a title).
_TITLE_CONNECTORS = {
    "and", "ve", "of", "the", "in", "on", "for", "with", "to",
    "a", "an", "ile",
}

# Turkish critical-edition descriptors — not part of the title proper.
_BOOK_FORM_WORDS = {
    "inceleme", "neşir", "tercüme", "translation", "study",
    "edition", "baskı", "hazırlık",
}


def _looks_like_given_name(seg: str) -> bool:
    """Return True if *seg* could be the given-name half of a
    ``Surname, Given`` pair: 1-4 words, no ``:``/``;``, no digits.

    Used by the year-at-end fallback to decide whether the author zone
    is 2 segments (Surname, Given) or 1 segment (institutional /
    mononym followed directly by the title)."""
    if ":" in seg or ";" in seg:
        return False
    if any(c.isdigit() for c in seg):
        return False
    words = seg.split()
    return 1 <= len(words) <= 4


def _is_title_segment(seg: str) -> bool:
    """Return True if *seg* is a title portion — not a translator note,
    not a book-form descriptor."""
    if not seg:
        return False
    if _is_likely_publisher_or_translator(seg):
        return False
    first_word = seg.split()[0].lower().rstrip(".,;:")
    if first_word in _BOOK_FORM_WORDS:
        return False
    if seg[0].isupper():
        return True
    if first_word in _TITLE_CONNECTORS:
        return True
    return False


def _find_year(text: str) -> Optional[re.Match]:
    """Return the match object for the first publication year found."""
    return _YEAR_RE.search(text)

def _find_date_marker(text: str) -> Optional[re.Match]:
    """Like ``_find_year`` but also accepts a no-date placeholder
    ``(t.y.)`` / ``(n.d.)``, whose position marks the author/year boundary."""
    m = _find_year(text)
    if m is not None:
        return m
    return _NO_DATE_RE.search(text)


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

    The trailing positive lookahead enforces that an alleged initial
    sequence must be followed by a delimiter (comma, semicolon, period,
    closing parenthesis, whitespace, or end of block). This is what
    distinguishes real initials from the leading letter of a full word:

      - ``"Smith, J."``          → initial ``J.`` ends at ``$`` → match.
      - ``"Kellogg, R. T."``     → initials end at ``$`` → match.
      - ``"Feldman, Walter"``    → ``W`` is followed by ``a`` → no match.
      - ``"Kılıç, Mahmud Erol"`` → ``M`` is followed by ``a`` → no match.
      - ``"Üçler Basımevi, İstanbul"`` → ``İ`` is followed by ``s`` → no match.

    Rejected matches fall through to ``_parse_first_last_token``, whose
    comma-handling branch turns ``"Surname, Given"`` into the equivalent
    ``"Surname, I."`` form.
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
        (?=[,;.)\s]|$)                  # must end at a delimiter
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

    # Comma-containing blocks use "Surname, Given[, ...]" ordering.
    # Take the first segment as the surname and the second as the given
    # name, if the given segment looks like a plausible personal name
    # (1-4 purely-alphabetic words, and not a publisher/translator
    # marker). Otherwise, return the surname alone as a mononym so
    # title fragments and publisher names never leak into the author
    # list. This branch also handles the case where ``_extract_last_first``
    # rejected the match because the alleged initial was actually the
    # first letter of a full given name ("Feldman, Walter, ..." →
    # "Feldman, W.").
    #
    # ``w.rstrip(".")`` strips a single trailing period so a given-name
    # word like "L." (an undotted-rest initial, e.g. "Karl L." from
    # "Signell, Karl L.") is accepted. Without this, the initial falls
    # through and the surname is returned without any initials
    # ("Signell" instead of "Signell, K. L.").
    if "," in token:
        parts = [p.strip() for p in token.split(",")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            surname = parts[0]
            given = parts[1]
            if not _is_likely_publisher_or_translator(given):
                given_words = given.split()
                if 1 <= len(given_words) <= 4 and all(
                    re.fullmatch(
                        r"[A-Za-zÀ-ÖØ-öø-ÿĀ-ſÇĞİÖŞÜçğıöşü'\-]+",
                        w.rstrip("."),
                    )
                    for w in given_words
                ):
                    initials = " ".join(
                        f"{w[0].upper()}." for w in given_words
                    )
                    return f"{surname}, {initials}"
            return surname

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


def _parse_author_block(block: str) -> list[str]:
    """
    Parse one chunk of an author list. The chunk is assumed to have
    been split at an '&' or 'and' conjunction, so it contains exactly
    one author name.

    Handles three forms:
      - 'Surname, Initials'  (Kellogg, R. T.)
      - 'Surname, Given'     (Kılıç, Mahmud Erol)
      - bare mononym        (Rosmawati)
    """
    block = block.strip().strip(",").strip()
    if not block:
        return []

    result = _extract_last_first(block)
    if result:
        return result

    # Bare mononym: no comma, one word, at least two characters.
    # Single-letter tokens are treated as initials, not names.
    if "," not in block and len(block.split()) == 1 and len(block) >= 2:
        return [block]

    parsed = _parse_first_last_token(block)
    if parsed:
        return [parsed]
    return []


def _is_name_segment(segment: str) -> bool:
    """Return True if *segment* looks like a name block (surname + given
    names / initials), not a title, publisher, or page-range fragment.

    Splits at author-list separators (``and`` / ``&``) with optional
    surrounding whitespace, because comma-splitting upstream strips the
    leading space before ``&`` (``"Kyle, K., & Crossley, S. A."`` →
    segments ``"Kyle"``, ``"K."``, ``"& Crossley"``, ``"S. A."``).
    ``\\s+(?:and|&)\\s+`` requires whitespace on both sides and silently
    rejects ``"& Crossley"``, dropping the second author.
    """
    cleaned = segment.strip().strip('",;:')
    if not cleaned:
        return False
    if _is_institutional_author(cleaned):
        return True
    if _is_likely_publisher_or_translator(cleaned):
        return False
    if re.search(r"\d", cleaned):
        return False
    if ":" in cleaned or ";" in cleaned:
        return False
    if len(cleaned) > 40:
        return False

    sub_parts = [
        p.strip()
        for p in re.split(r"\s*(?:\band\b|&)\s*", cleaned)
        if p.strip()
    ]
    if not sub_parts:
        return False
    for part in sub_parts:
        words = part.split()
        if not words or len(words) > 4:
            return False
        for word in words:
            core = word.rstrip(".,;:")
            if not core:
                return False
            if re.fullmatch(r"(?:[A-Z]\.?(?:-[A-Z]\.?)*)+", core):
                continue
            if re.fullmatch(
                r"[A-ZÀ-ÖØ-ÞĀ-ſ][a-zA-ZÀ-ÖØ-öø-ÿĀ-ſ'\-]*", core,
            ):
                continue
            if core.lower() in _NAME_PARTICLES:
                continue
            return False
    return True


def _is_institutional_author(segment: str) -> bool:
    """Return True if *segment* is a recognised institutional author
    (Türk Dil Kurumu, TBMM, …). See ``_INSTITUTIONAL_AUTHOR_RE``."""
    return bool(_INSTITUTIONAL_AUTHOR_RE.fullmatch(segment.strip()))


def extract_authors(text: str) -> list[str]:
    """
    Extract authors from a bibliographic reference string.

    Supports APA, MLA, Chicago, IEEE, and common publisher formats.
    Returns a list of authors in ``Surname, X. Y.`` format (initials
    always dotted and space‑separated).

    Single-name institutional authors ("Türk Dil Kurumu", "IATA",
    "Euronews") are returned as-is. Reference styles always separate
    personal surnames from initials with a comma, so absence of a
    comma means the block is a single institutional name. For known
    institutional authors that appear comma-separated from their title
    (Türk Dil Kurumu, TBMM, …), the institutional name is returned and
    the title segment is not parsed as a given name.
    """
    text = _ACCESS_TAIL_RE.sub("", text).rstrip()
    year_match = _find_date_marker(text)
    if year_match is None:
        return []

    author_part = text[: year_match.start()].strip()
    if not author_part:
        return []

    # Trailing comma/space is common when the raw text reads "IATA, (2024),".
    # Also strip a dangling "(" left behind when the year form is
    # "(YYYY, Month Day)": _YEAR_RE's conditional requires ")" after the
    # year, so for a comma-separated month/day it matches the bare year
    # and leaves the "(" at the end of author_part ("Yedikardeş, C. (").
    # Without this, _is_name_segment rejects the "C. (" segment and the
    # truncation loop collapses the author to the surname alone.
    author_part = author_part.rstrip(", \t(")

    # Institutional author: no comma means the block cannot be a
    # "Surname, Initials" list. Strip any leftover opening bracket that
    # a year-in-parens regex may have left behind ("Euronews. (").
    if "," not in author_part:
        institutional = author_part.rstrip(". ([{")
        if institutional:
            return [institutional]

    # Institutional author with a title: "Türk Dil Kurumu, Türkçe
    # Sözlük, Milliyet Yayınları, İstanbul 1992." The first segment is
    # the institution, the rest is title/publisher/city. Without this
    # check, ``_parse_first_last_token`` reads "Türkçe Sözlük" as a
    # given name and produces the phantom author
    # "Türk Dil Kurumu, T. S.".
    segments = author_part.split(",")
    if segments and _is_institutional_author(segments[0]):
        return [segments[0].strip()]

    # Harvard-style year-at-end entries sandwich title, journal, and
    # publisher between the authors and the year:
    #     Wright, Owen, "A Preliminary Version …", Bulletin of the School
    #     of Oriental and African Studies, Cilt 58, Sayı 3, 1995, s. 455-478.
    # Truncate at the first comma-separated segment that is not name-like,
    # so the subsequent '&'/'and' splitter cannot mistake an "and" inside
    # the title or journal for an author separator. In APA-style entries
    # (where the year sits in parentheses immediately after the authors)
    # author_part is already clean and every segment is name-like, so
    # truncation is a no-op. Guard with ``if kept:`` so a single-segment
    # institutional author is not silently dropped by an over-eager
    # truncation.
    kept: list[str] = []
    for seg in segments:
        stripped = seg.strip()
        if not stripped:
            continue
        if _is_name_segment(stripped):
            kept.append(stripped)
        else:
            break
    if kept:
        author_part = ", ".join(kept)

    # Split the author list at '&' and 'and' boundaries. Splitting
    # before normalisation preserves mononym authors (Rosmawati) that
    # would otherwise be swallowed when '&' is replaced by a comma:
    # 'Rosmawati, & Lowie, W.' collapses to 'Rosmawati, Lowie, W.'
    # and the parser reads 'Rosmawati' + 'L' (from 'Lowie') as one
    # author, dropping Lowie entirely.
    blocks = _AND_AMPERSAND_RE.split(author_part)

    authors: list[str] = []
    for block in blocks:
        authors.extend(_parse_author_block(block))

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
    - Harvard year-at-end style: ``Surname, Given, Title, Publisher,
      City Year.`` with a publisher marker or a ``City Year`` tail.
    - No-date APA web style: ``Author. (t.y.). Title. <access-statement>``.
    """

    # Drop contributor/role notes before any title pattern runs — see
    # _ROLE_NOTE_RE. Must precede Pattern 1/2/3 so their ". Capital"
    # terminators do not fire inside the note.
    text = _ROLE_NOTE_RE.sub("", text)

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

    # --- Pattern 1a: no-date placeholder (t.y.) / (n.d.) ---------------------
    #   IMDb. (t.y.). Yüzüklerin Efendisi. 18 Ocak 2026 tarihinde …
    #   Author. (n.d.). Title. Retrieved …
    # Self-contained: works whether or not the access tail was stripped.
    # The lookahead accepts: (a) an access statement beginning "N Mon YYYY
    # tarihinde", (b) a sentence break ". Capital", or (c) end of string.
    nd_m = re.search(
        r"\((?:t\.y\.|n\.d\.)\)\.\s*(.+?)"
        r"(?:\.\s+\d{1,2}\s+\S+\s+\d{4}\s+tarihinde"
        r"|\.\s+[A-Z]"
        r"|\.\s*$)",
        text,
        re.IGNORECASE,
    )
    if nd_m:
        candidate = nd_m.group(1).strip()
        if candidate and not _is_likely_page_fragment(candidate):
            return _clean_title(candidate, text)

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

    # --- Pattern 2a: title ending with ? or ! -------------------------------
    #   (2000). The episodic buffer: A new component of working memory?
    #   Trends in cognitive sciences, 4(11), 417-423. https://doi.org/…
    # Pattern 2 requires a "." terminator; a "?" title falls through and
    # ends up empty. Preserve the terminal punctuation (part of the title)
    # and require the next token to be a capitalised word or end-of-string,
    # so the following journal name is not swallowed.
    m = re.search(r"\(\d{4}[a-z]?\)\.\s*(.+?[?!])(?=\s+[A-Z]|\s*$)", text)
    if m:
        title = m.group(1).strip()
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

    # --- Final fallback: year-at-end (Harvard/Chicago) styles ---------------
    year_match = _find_year(text)
    if year_match:
        pre_year = text[: year_match.start()].strip()
        tail_after = text[year_match.end():].strip()
        is_year_at_end = tail_after.rstrip(".").strip() == ""

        # (i) Prefer a fully-quoted title (Harvard/Chicago year-at-end style):
        #   Wright, Owen, "A Preliminary Version of the Kitāb al-Adwār",
        #   Bulletin of the School of Oriental and African Studies,
        #   Cilt 58, Sayı 3, 1995, s. 455-478.
        # Without this branch, the longest-candidate heuristic below
        # picks the journal name (the longest comma-separated segment)
        # as the title.
        quoted_title = re.search(r'[.,]\s*"([^"]{5,})"\s*(?:,|$)', pre_year)
        if quoted_title:
            candidate = quoted_title.group(1).strip()
            if candidate and not _is_likely_page_fragment(candidate):
                return _clean_title(candidate, text)

        # (ii) Year-at-end with publisher + city: title is everything
        # between the last author and the second-to-last segment (the
        # publisher). This recovers comma-containing titles that the
        # longest-candidate heuristic truncates at the first comma:
        #   Wright, Owen, The Modal System of Arab and Persian Music,
        #   A.D. 1250-1300, Oxford University Press, Oxford 1978.
        # and:
        #   Feldman, Walter, From Rumi to the Whirling Dervishes: Music,
        #   Poetry, and Mysticism in the Ottoman Empire, Edinburgh
        #   University Press, Edinburgh 2022.
        if is_year_at_end:
            segments = [s.strip() for s in pre_year.split(",") if s.strip()]
            if len(segments) >= 3:
                # Author zone: 1 segment for institutional authors or
                # mononym+title (no given name follows); 2 segments for
                # the standard "Surname, Given" pair. ``_is_name_segment``
                # is deliberately not used here — it accepts title-like
                # segments ("Sayıların Gizemi", "Kitâbü'l-Edvâr") as
                # names, dragging the whole title into the author zone.
                if _is_institutional_author(segments[0]):
                    author_end_idx = 1
                elif not _looks_like_given_name(segments[1]):
                    author_end_idx = 1
                else:
                    author_end_idx = 2
                publisher_idx = len(segments) - 2
                if author_end_idx < publisher_idx:
                    title_parts = [
                        p for p in segments[author_end_idx:publisher_idx]
                        if _is_title_segment(p)
                    ]
                    if title_parts:
                        candidate = ", ".join(title_parts).strip(", .;:")
                        if candidate and not _is_likely_page_fragment(candidate):
                            return _clean_title(candidate, text)

        # (iii) Longest candidate (pre-existing heuristic, kept as the
        # last-resort fallback so no currently-working behavior changes).
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
            if not _is_likely_publisher_or_translator(best_candidate):
                return _clean_title(best_candidate, text)

    return None


def extract_journal(text: str) -> str | None:
    """
    Extract journal name from a journal-article reference.

    Journal names sit immediately before a volume/issue marker:

        "... Title. Journal Name, Vol. 13 No. 6, pp. 1312-1333."
        "... Title. Journal Name, 11(4), 467-469."
        "... Title. Journal Name, 1(2), 116-125."
        '... "Title", Journal Name, Cilt 58, Sayı 3, 1995, s. 455-478.'
        '... "Title", Journal Name, Sayı 10, 1972, s. 83-97.'

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

    # Pattern D: Turkish "Journal Name, Cilt N" or "Journal Name, Sayı N".
    # Anchored on the closing quote of the article title (or a ")" / "."
    # / "]" boundary), which is what distinguishes the journal from any
    # quoted title fragment. Handles the two shapes Turkish journals use:
    #
    #     "Title", Rast Müzikoloji Dergisi, Cilt 2, Sayı 1, 2014, s. 1-49.
    #     "Title", Porte Akademik Müzik ve Dans Araştırmaları Dergisi,
    #         Sayı 10, 2014, s. 9-36.
    #
    # The reluctant ``[^.;!?]*?`` stops at the first sentence-ending
    # punctuation so a title-internal period cannot drag the match
    # backward into the title. Anchoring on a non-start boundary (quote,
    # paren, bracket) prevents the pattern from firing on unquoted
    # Harvard refs whose pre-year segments look like name pairs.
    m = re.search(
        r'(?:[.")\]]\s*,?\s+)'
        r'([A-ZÇĞİÖŞÜ][^.;!?]*?),\s*(?:Cilt|Sayı)\s+\d+',
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

    Supports the markers used across our fixtures:

        "Journal Name, Vol. 13 No. 6, ..."  -> "13"  (Harvard)
        "Journal Name, 11(4), 467-469."     -> "11"  (APA)
        "Journal Name, Cilt 57, Sayı 3"     -> "57"  (Turkish)

    Returns the volume as a string, or None if no pattern matched.
    """
    # Harvard-style: "Vol. 13" or "Vol. 13A"
    m = re.search(r"\bVol\.\s*(\d+[A-Za-z]?)", text)
    if m:
        return m.group(1)

    # Turkish: "Cilt N, Sayı M" — both markers required. A bare
    # "Cilt N" (as in book-chapter "(Cilt 3, s. 321)") is book-series
    # volume metadata, not a journal volume, and must not be reported
    # as one.
    m = re.search(r"\bCilt\s+(\d+[A-Za-z]?)\s*,\s*Sayı\s+\d+", text)
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

    Supports the markers used across our fixtures:

        "Journal Name, Vol. 13 No. 6, ..."      -> "6"  (Harvard)
        "Journal Name, 11(4), 467-469."         -> "4"  (APA)
        "Journal Name, Cilt 6, Sayı 11, 2008"   -> "11" (Turkish)

    Returns the issue as a string, or None if no pattern matched.
    """
    # Harvard-style: "No. 6" or "No. 6A"
    m = re.search(r"\bNo\.\s*(\d+[A-Za-z]?)", text)
    if m:
        return m.group(1)

    # Turkish: "Sayı 11" or "Sayı 11A"
    m = re.search(r"\bSayı\s+(\d+[A-Za-z]?)", text)
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
        "... Cilt 58, Sayı 3, 1995, s. 455-478." -> "455-478"  (Turkish)

    Preserves the dash character as it appears in the raw text
    (hyphen, en-dash). Returns None if no range matched.
    """
    # Pattern A: "pp. NNN-NNN" (Harvard and book-chapter styles)
    m = re.search(r"\bpp\.\s*(\d+\s*[-–]\s*\d+)", text)
    if m:
        return m.group(1).replace(" ", "")

    # Pattern A2: "s. NNN-NNN" (Turkish page marker)
    m = re.search(r"\bs\.\s*(\d+\s*[-–]\s*\d+)", text)
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
    four separate anchors, tried in order, each targeted at a specific
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

    D. Western publishers ending in a known English marker, at the end
       of the string.

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
    #    "... Publishers", "... Books", "... Publications". Excluding "(" and
    #    ")" from the body stops a match from spanning a preceding
    #    contributor/role parenthetical — e.g. the Flick shape
    #    "(N. K. Denzin, & Y. S. Lincoln, Dü) SAGE Publications." must
    #    yield "SAGE Publications", not "Lincoln, Dü) SAGE Publications".
    m = re.search(
        r"([A-Z][^.;:()]*(?:Press|Publishing|Publishers|Books|Publications))"
        r"\.\s*$",
        text,
    )
    if m:
        return m.group(1).strip()

    return None


def extract_book_title(text: str) -> str | None:
    """
    Extract the book title from a book-chapter reference.

    APA style places the chapter title immediately after the year and
    the book title after the editor list, terminated by the page-range
    parenthetical:

        Kellogg, R. T. (1996). A model of working memory in writing.
        In C. M. Levy & S. Ransdell (Eds.), The science of writing:
        Theories, methods, individual differences, and applications
        (pp. 57-71). Lawrence Erlbaum Associates, Inc.

    The book title is ``The science of writing: Theories, methods,
    individual differences, and applications``.

    Recognised editor markers: ``(Ed.)``, ``(Eds.)``, ``(Ed)``,
    ``(Eds)``, ``(Haz.)``, ``(Haz)``, ``(Cilt N)``. If the reference
    does not have the ``In <editors>, BOOK TITLE (pp. N-N)`` shape,
    returns None.
    """
    pattern = re.compile(
        r"\bIn\s+.+?\((?:Eds?\.?|Haz\.?|Cilt\s+\d+)\)\s*,\s*"
        r"(.+?)\s*\(pp\.\s*\d+",
        re.IGNORECASE | re.UNICODE,
    )
    m = pattern.search(text)
    if not m:
        return None
    candidate = m.group(1).strip().rstrip(".,;")
    return candidate or None


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

    Trailing parentheticals are stripped ONLY when they are clearly
    edition, translator, or editor notes ("(2. baskı)", "(I. Melikoff,
    Çev.)", "(Eds.)"). A parenthetical that is part of the title itself
    is preserved — "Çengname'de Musikî Terimleri (Perde, Nağme, Makam,
    Seyir, Şube, Terkip, Avaz)" must not lose its closing parenthetical.

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

    # Strip trailing parentheticals that are edition / translator /
    # editor / numeric-metadata markers. A bare parenthetical with only
    # content words ("(Perde, Nağme, …)") is preserved as part of the
    # title. Numeric-annotation forms ("(Sayı: 12362)") are stripped.
    _edition_note = re.compile(
        r"\s*\([^)]*(?:"
        r"\b(?:bask[ıi]|çev|haz|trans|eds?)"
        r"|:\s*\d"
        r"|\bpp?\.\s*\d"
        r"|\bs\.\s*\d"
        r"|\b\d+\.\s*b\."
        r")[^)]*\)\s*$",
        re.IGNORECASE,
    )
    title = _edition_note.sub("", title).strip()

    # Strip a trailing chapter-in-book tail: the chapter title must stop
    # at the ". In " before the editor list. Book title proper is handled
    # by extract_book_title; this only cleans reference.title.
    #   "…SLA. In P. Robinson (Ed.), Cognition and Second Language Instruction"
    title = re.sub(
        r"\.\s+In\s+(?:[A-Z]\.\s*)+[^()]*\((?:Eds?\.?|Haz\.?)\)[\s\S]*$",
        "",
        title,
    ).strip()

    # Strip trailing journal detail glued to a title: "Journal, N(M)" or
    # "Journal, N, N-N" or "Journal, Vol. N". Covers
    #   "… Art? Arts, 7(2)." (Hertzmann)
    #   "… performance, IRAL, 45, 161-176" (Robinson & Gilabert)
    title = re.sub(
        r"[,.]?\s+[A-ZÇĞİÖŞÜ][\wÇĞİÖŞÜçğıöşü\s]{2,40},\s*"
        r"(?:Vol\.\s*\d+|\d+\(\d+\)"
        r"|\d+,\s*\d+\s*[-–]\s*\d+)"
        r"\.?\s*$",
        "",
        title,
    ).strip()

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