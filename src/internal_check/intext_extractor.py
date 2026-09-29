"""
In-text citation extractor.

Finds citations in manuscript body text. Three kinds are supported:

    Parenthetical:  (Smith, 2020), (Smith & Jones, 2020),
                    (Smith et al., 2020; Jones, 2019)
    Narrative:      According to Smith (2020),
                    Smith (2020) argues,
                    Smith (2020, p. 45)
    Numeric:        [1], [1-3], [1,3,5]

Statistical expressions like ``(M = 2.985; SD = 1.0345)`` are rejected
by the noise filter and never reach the citation parser.

Language-specific markers (conjunctions, "et al.", narrative phrases)
are read from a CitationProfile. The extractor itself contains no
hard-coded English or Turkish words.

The extractor does not see the reference list. Numeric citations are
returned as plain integers; mapping them to reference entries is the
matcher's job.
"""

import re

from .models import (
    CitationKind,
    InTextCitation,
)
from .noise_filter import is_non_citation
from .profiles import (
    CitationProfile,
    GENERIC,
)


# A 4-digit year, optionally followed by a lowercase letter suffix (2020a).
_YEAR_RE = re.compile(r"\b((?:19|20)\d{2})([a-z]?)\b")

# A parenthetical that *starts* with a year, e.g. "(2020)", "(2020a)",
# "(2020, p. 45)". Used to detect narrative citations.
_STARTS_WITH_YEAR_RE = re.compile(r"^((?:19|20)\d{2})([a-z]?)(?:[,\s]|$)")

# Content of a bracket or parenthetical that is a numeric citation.
# Accepts "1", "1,2", "1;2", "1-3", "1–3", "1, 3-5".
_NUMERIC_RE = re.compile(r"^\d+(\s*[,;\-–]\s*\d+)*$")

# One component of a numeric list, either a single number or a range.
_NUMERIC_PART_RE = re.compile(r"^\s*(\d+)\s*(?:[-–]\s*(\d+))?\s*$")

# Trailing punctuation to strip from an author phrase.
_TRAILING_PUNCT_RE = re.compile(r"[\s,;:]+$")

# Maximum number of words to look back when hunting for a narrative author.
_NARRATIVE_LOOKBACK_WORDS = 8


class InTextExtractor:
    """
    Extracts in-text citations from a manuscript.
    """

    def __init__(self, profile: CitationProfile = GENERIC) -> None:
        self.profile = profile
        self._unparsed: list[tuple[str, str]] = []

    @property
    def unparsed(self) -> list[tuple[str, str]]:
        """
        Parenthetical segments that were not recognized as citations.

        Each entry is ``(text, location)``. Populated by the most recent
        call to :meth:`extract` or :meth:`extract_text`.
        """
        return list(self._unparsed)

    def extract(self, paragraphs: list[str]) -> list[InTextCitation]:
        """
        Extract citations from a list of paragraph strings.

        Args:
            paragraphs:
                Body-text paragraphs, in document order. Must not
                include the references section.

        Returns:
            A list of :class:`InTextCitation` objects in document order.
        """
        self._unparsed = []
        citations: list[InTextCitation] = []

        for idx, paragraph in enumerate(paragraphs):
            if not paragraph:
                continue
            location = f"paragraph {idx + 1}"
            citations.extend(self._extract_from_text(paragraph, location))

        return citations

    def extract_text(self, body_text: str) -> list[InTextCitation]:
        """
        Convenience wrapper: split *body_text* on blank lines into
        paragraphs and delegate to :meth:`extract`.
        """
        paragraphs = re.split(r"\n\s*\n", body_text)
        return self.extract([p.strip() for p in paragraphs if p.strip()])

    # ------------------------------------------------------------------
    # Per-paragraph extraction
    # ------------------------------------------------------------------

    def _extract_from_text(
        self, text: str, location: str,
    ) -> list[InTextCitation]:
        citations: list[InTextCitation] = []

        for match in re.finditer(r"\(([^()]*)\)", text):
            content = match.group(1).strip()
            if not content:
                continue
            citations.extend(
                self._handle_parenthetical(
                    content=content,
                    raw=match.group(0),
                    text=text,
                    start=match.start(),
                    location=location,
                )
            )

        for match in re.finditer(r"\[([^\[\]]*)\]", text):
            content = match.group(1).strip()
            if not content:
                continue
            nums = self._expand_numeric(content)
            if nums:
                citations.append(
                    InTextCitation(
                        raw=match.group(0),
                        kind=CitationKind.NUMERIC,
                        numbers=nums,
                        location=location,
                        confidence=0.99,
                    )
                )
            else:
                self._unparsed.append((match.group(0), location))

        return citations

    def _handle_parenthetical(
        self,
        content: str,
        raw: str,
        text: str,
        start: int,
        location: str,
    ) -> list[InTextCitation]:
        """Decide what kind of citation a parenthetical holds."""
        citations: list[InTextCitation] = []

        # Case 1: parenthetical that starts with a year -> narrative citation.
        year_at_start = _STARTS_WITH_YEAR_RE.match(content)
        if year_at_start:
            year = int(year_at_start.group(1))
            suffix = year_at_start.group(2) or None
            authors = self._find_narrative_authors(text, start)
            if authors:
                confidence = (
                    0.85 if self._has_leading_marker(text, start) else 0.6
                )
                citations.append(
                    InTextCitation(
                        raw=raw,
                        kind=CitationKind.NARRATIVE,
                        authors=authors,
                        year=year,
                        year_suffix=suffix,
                        location=location,
                        confidence=confidence,
                    )
                )
            else:
                self._unparsed.append((raw, location))
            return citations

        # Case 2: author-year parenthetical, possibly with semicolons.
        for seg in re.split(r"\s*[;|]\s*", content):
            seg = seg.strip()
            if not seg:
                continue
            if is_non_citation(seg):
                continue

            year_matches = list(_YEAR_RE.finditer(seg))
            if not year_matches:
                self._unparsed.append((f"({seg})", location))
                continue

            first = year_matches[0]
            author_part = seg[: first.start()].strip()
            author_part = _TRAILING_PUNCT_RE.sub("", author_part)
            author_part = self._strip_leading_markers(author_part)

            if not author_part:
                self._unparsed.append((f"({seg})", location))
                continue

            authors = self._split_authors(author_part)
            if not authors:
                self._unparsed.append((f"({seg})", location))
                continue

            # Decide which of the remaining years belong to the same
            # author. A year belongs iff the text between the previous
            # kept year and this year is only commas and whitespace.
            #
            #   "(Köhler, 1986, 2012)"     -> two citations
            #   "(Smith, 2020a, 2020b)"    -> two citations (with suffix)
            #   "(Smith, 2020, p. 1945)"   -> one citation (page locator)
            kept = [first]
            for m in year_matches[1:]:
                between = seg[kept[-1].end(): m.start()]
                if re.fullmatch(r"[\s,]+", between):
                    kept.append(m)
                else:
                    break

            for m in kept:
                year = int(m.group(1))
                suffix = m.group(2) or None
                citations.append(
                    InTextCitation(
                        raw=f"({seg})",
                        kind=CitationKind.PARENTHETICAL,
                        authors=list(authors),
                        year=year,
                        year_suffix=suffix,
                        location=location,
                        confidence=0.95,
                    )
                )

        return citations

    # ------------------------------------------------------------------
    # Author-phrase handling
    # ------------------------------------------------------------------

    def _split_authors(self, author_part: str) -> list[str]:
        """
        Split an author phrase into individual authors.

        Uses the profile's conjunctions and et-al markers. "et al." is
        removed entirely; it is a marker, not an author name.
        """
        text = author_part

        # Remove et-al markers (longest first, so "ve ark." beats "vd.").
        for marker in sorted(
            self.profile.et_al_markers, key=len, reverse=True,
        ):
            text = re.sub(
                re.escape(marker),
                "",
                text,
                flags=re.IGNORECASE,
            )

        # Normalise conjunctions to commas.
        for conj in sorted(
            self.profile.conjunctions, key=len, reverse=True,
        ):
            text = re.sub(
                rf"(?<!\w){re.escape(conj)}(?!\w)",
                ",",
                text,
                flags=re.IGNORECASE,
            )

        text = re.sub(r"\s*,\s*", ",", text)
        text = text.strip(" ,;")

        if not text:
            return []

        return [p.strip() for p in text.split(",") if p.strip()]

    def _strip_leading_markers(self, text: str) -> str:
        """Remove any narrative_leading phrase from the start of *text*."""
        stripped = text.strip()
        if not stripped:
            return ""

        lowered = stripped.casefold()
        for marker in sorted(
            self.profile.narrative_leading, key=len, reverse=True,
        ):
            m_lower = marker.casefold()
            if lowered == m_lower:
                return ""
            if lowered.startswith(m_lower + " "):
                return stripped[len(marker) + 1:].lstrip()
            if lowered.startswith(m_lower + ","):
                return stripped[len(marker) + 1:].lstrip()

        return stripped

    def _find_narrative_authors(
        self, text: str, paren_start: int,
    ) -> list[str]:
        """
        Look up to :data:`_NARRATIVE_LOOKBACK_WORDS` words before
        *paren_start* for a likely author phrase, then split it into
        individual surnames via the profile's conjunctions and
        et-al markers.

        Walks backwards from the parenthesis, collecting tokens that
        are capitalized words, profile conjunctions ("and", "ve"), or
        parts of profile et-al markers ("et al.", "vd."). Stops at the
        first token that is none of those. This recovers multi-author
        phrases ("Smith and Jones") and et-al phrases ("Smith et al.")
        without over-collecting sentence content.

        Returns an empty list if no plausible author phrase is found.
        """
        prefix = text[:paren_start].rstrip()
        if not prefix:
            return []

        tokens = prefix.split()
        window = tokens[-_NARRATIVE_LOOKBACK_WORDS:]

        conjunctions_lower = frozenset(
            c.casefold() for c in self.profile.conjunctions
        )
        et_al_parts = self._et_al_token_parts()

        collected: list[str] = []
        for token in reversed(window):
            bare = token.strip(".,;:()[]'\"\u2019\u2018")
            if not bare:
                break
            bare_lower = bare.casefold()
            if bare_lower in conjunctions_lower:
                collected.append(token)
                continue
            if bare_lower in et_al_parts:
                collected.append(token)
                continue
            if bare[0].isalpha() and bare[0].isupper():
                collected.append(token)
                continue
            break

        if not collected:
            return []

        collected.reverse()
        phrase = " ".join(collected)
        phrase = self._strip_leading_markers(phrase)
        if not phrase:
            return []

        return self._split_authors(phrase)

    def _et_al_token_parts(self) -> frozenset[str]:
        """
        Individual words that make up multi-word et-al markers,
        lowercased and stripped of punctuation.

        ``"et al."``   contributes ``{"et", "al"}``.
        ``"ve ark."``  contributes ``{"ve", "ark"}``.
        """
        parts: set[str] = set()
        for marker in self.profile.et_al_markers:
            for piece in marker.split():
                piece = piece.strip(".,;:").casefold()
                if piece:
                    parts.add(piece)
        return frozenset(parts)

    def _has_leading_marker(self, text: str, paren_start: int) -> bool:
        """Return True if a narrative_leading marker precedes the paren."""
        prefix = text[:paren_start].rstrip()
        if not prefix:
            return False

        window_text = " ".join(
            prefix.split()[-_NARRATIVE_LOOKBACK_WORDS:]
        )
        lowered = window_text.casefold()
        for marker in self.profile.narrative_leading:
            m_lower = marker.casefold()
            if lowered == m_lower or lowered.startswith(m_lower + " "):
                return True
            if lowered.startswith(m_lower + ","):
                return True

        return False

    # ------------------------------------------------------------------
    # Numeric handling
    # ------------------------------------------------------------------

    def _expand_numeric(self, content: str) -> list[int]:
        """
        Expand a numeric-citation content string into a list of integers.

        ``"1"``       -> ``[1]``
        ``"1,2"``     -> ``[1, 2]``
        ``"1-3"``     -> ``[1, 2, 3]``
        ``"1,3-5"``   -> ``[1, 3, 4, 5]``
        ``"2020"``    -> ``[]``  (looks like a year, not a reference number)
        ``"foo"``     -> ``[]``
        """
        content = content.strip()
        if not content:
            return []
        if not _NUMERIC_RE.match(content):
            return []

        # Reject a single 4-digit number in the range 1900–2100 —
        # almost certainly a year, not a reference number.
        if content.isdigit() and len(content) == 4:
            n = int(content)
            if 1900 <= n <= 2100:
                return []

        result: list[int] = []
        for part in re.split(r"[,;]", content):
            part = part.strip()
            if not part:
                continue
            m = _NUMERIC_PART_RE.match(part)
            if not m:
                return []
            start = int(m.group(1))
            if m.group(2):
                end = int(m.group(2))
                if end < start:
                    return []
                result.extend(range(start, end + 1))
            else:
                result.append(start)

        return result