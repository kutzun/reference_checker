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
    ALL_LOOKBACK_CONJUNCTIONS,
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

# Lowercase surname particles used across European and Arabic-transliterated
# names (de Bot, van der Berg, von Neumann, del Toro). Included in a
# narrative phrase when found immediately before the surname.
_SURNAME_PARTICLES = frozenset({
    "de", "van", "der", "den", "von", "da", "del", "della", "di",
    "la", "le", "du", "dos", "das", "ter", "ten", "op", "zu", "bin",
})

# Uppercase words that may appear immediately before a surname in
# ordinary prose but are not part of a compound surname. Blocks the
# narrative walk from extending "Brown (2020)" into "As Brown" when
# the sentence starts with "As"/"See"/"In". Lowercase for comparison.
# Turkish function words are included so the same guard works under
# the TURKISH profile when a sentence starts with "Gibi", "İçin", etc.
_COMPOUND_SURNAME_BLOCKERS = frozenset({
    # English function words / sentence starters
    "as", "at", "by", "cf", "for", "from", "in", "into", "of", "on",
    "or", "so", "to", "via", "with", "the", "a", "an", "and", "but",
    "yet", "if", "when", "while", "after", "before", "since", "during",
    "because", "although", "though", "whereas", "however", "therefore",
    "thus", "moreover", "furthermore", "consequently", "nevertheless",
    "according", "following", "citing", "quoted", "see", "also",
    "this", "that", "these", "those", "it", "we", "i", "you", "they",
    "he", "she", "his", "her", "its", "their",
    # Turkish function words / sentence starters
    "ile", "gibi", "için", "veya", "ya", "ama", "fakat", "lakin",
    "çünkü", "ancak", "oysa", "halbuki", "ayrıca", "üstelik",
    "sonra", "önce", "kadar", "göre", "dair", "ilişkin", "yönelik",
    "olarak", "üzere", "dolayı", "ötürü", "rağmen", "karşın",
})

# Maximum number of words to look back when hunting for a narrative author.
_NARRATIVE_LOOKBACK_WORDS = 8

# Maximum number of compound-surname extensions the narrative walk may
# perform in one pass. Two covers "Ercan Güven & Öztürk Pat (2020)"
# without risking three-word over-capture on ordinary prose.
_MAX_COMPOUND_EXTENSIONS = 2

# Bounded window used when capturing an unbalanced orphan '('. Keeps
# the unparsed list readable when a paren is never closed.
_ORPHAN_CAPTURE_CHARS = 200


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
        consumed_spans: list[tuple[int, int]] = []

        for match in re.finditer(r"\(([^()]*)\)", text):
            consumed_spans.append((match.start(), match.end()))
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

        self._flag_orphan_parens(text, consumed_spans, location)

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

    def _flag_orphan_parens(
        self,
        text: str,
        consumed_spans: list[tuple[int, int]],
        location: str,
    ) -> None:
        """
        Flag orphan ``(`` characters not consumed by the well-formed
        parenthetical regex.

        A well-formed match is one whose content contains no nested
        ``(``. When a citation contains a nested parenthesis - either
        balanced (``(Özgüç, 1980, s. 465 (Yenihayat), ...)``) or
        unbalanced (``(Keskin, 2009, ... (Bilgi, 1999, ...)`` with no
        close on the outer) - the outer parens are skipped by the
        extraction regex, and the citation content would otherwise be
        silently lost. Editors would see the corresponding reference
        reported as Uncited with no indication of where it is cited.

        To avoid flooding the unparsed list with non-citation nested
        parens (math expressions like ``(p < 0.05 (two-tailed))``),
        the captured content is only flagged if it contains a
        plausible 4-digit year. ``_YEAR_RE`` requires 19xx or 20xx,
        so figures like ``Fig. 91/16`` do not trigger the flag.
        """
        starts = {s for s, _ in consumed_spans}
        flagged_spans: list[tuple[int, int]] = []

        for i, ch in enumerate(text):
            if ch != "(":
                continue
            if i in starts:
                continue
            if any(s <= i < e for s, e in consumed_spans):
                continue
            if any(s <= i < e for s, e in flagged_spans):
                continue

            captured = self._capture_paren(text, i)
            if not captured:
                continue
            if not _YEAR_RE.search(captured):
                continue

            flagged_spans.append((i, i + len(captured)))
            self._unparsed.append((captured, location))

    @staticmethod
    def _capture_paren(text: str, start: int) -> str:
        """
        Return the content of the paren opening at ``start``.

        Balanced parens are captured up to and including their
        matching close. Unbalanced opens (no matching close anywhere
        in ``text``) are captured from ``start`` to a bounded window
        of :data:`_ORPHAN_CAPTURE_CHARS` characters or the end of the
        paragraph, whichever is shorter - enough for the editor to
        see what the malformed citation contains.
        """
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]

        end = min(start + _ORPHAN_CAPTURE_CHARS, len(text))
        return text[start:end]

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
            authors, display_phrase, _has_foreign_conj = (
                self._find_narrative_authors(text, start)
            )
            if not authors:
                self._unparsed.append((raw, location))
                return citations

            confidence = (
                0.85 if self._has_leading_marker(text, start) else 0.6
            )

            # APA: "Smith (1998, 2009)" = two works, one per year.
            # Mirror Case 2's kept-loop so trailing years are not
            # silently dropped when the segment starts with a year.
            year_matches = list(_YEAR_RE.finditer(content))
            kept = [year_matches[0]]
            for m in year_matches[1:]:
                between = content[kept[-1].end(): m.start()]
                if re.fullmatch(r"[\s,]+", between):
                    kept.append(m)
                else:
                    break

            for m in kept:
                citations.append(
                    InTextCitation(
                        raw=(
                            f"{display_phrase} {raw}"
                            if display_phrase
                            else raw
                        ),
                        kind=CitationKind.NARRATIVE,
                        authors=list(authors),
                        year=int(m.group(1)),
                        year_suffix=m.group(2) or None,
                        location=location,
                        confidence=confidence,
                    )
                )
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
            if conj == "&":
                # "&" separates authors with or without surrounding
                # whitespace: "Coe & Ziegelman" and "Coe& Ziegelman"
                # both occur in manuscripts. The generic lookbehind
                # (?<!\w)&(?!\w) requires non-word on both sides and
                # rejects "Coe& Ziegelman". Requiring whitespace on at
                # least one side is safe: real ampersand-in-name uses
                # (AT&T, R&D, H&M) have no surrounding whitespace at all.
                text = re.sub(r"(?:&\s+|\s+&)", ", ", text)
            else:
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

    def _walk_narrative_phrase(
        self,
        text: str,
        paren_start: int,
        conjunctions: frozenset[str],
    ) -> str:
        """
        Walk backwards from *paren_start* over up to
        :data:`_NARRATIVE_LOOKBACK_WORDS` words, collecting a plausible
        author phrase. *conjunctions* is the set of conjunction words
        the walk will step over when moving to the previous author.

        Returns the collected phrase as a single space-joined string,
        or "" if no plausible author phrase was found.
        """
        prefix = text[:paren_start].rstrip()
        if not prefix:
            return ""

        tokens = prefix.split()
        window = tokens[-_NARRATIVE_LOOKBACK_WORDS:]

        conjunctions_lower = frozenset(
            c.casefold() for c in conjunctions
        )
        et_al_parts = self._et_al_token_parts()

        EXPECT_SURNAME = 0
        EXPECT_EXTENSION = 1
        state = EXPECT_SURNAME

        collected: list[str] = []
        compound_extensions = 0
        n = len(window)
        for idx in range(n - 1, -1, -1):
            token = window[idx]
            bare = token.strip(".,;:()[]'\"\u2019\u2018")
            if not bare:
                break
            bare_lower = bare.casefold()

            if state == EXPECT_SURNAME:
                if bare_lower in et_al_parts:
                    collected.append(token)
                    continue
                if bare[0].isalpha() and bare[0].isupper():
                    collected.append(token)
                    state = EXPECT_EXTENSION
                    continue
                break

            # state == EXPECT_EXTENSION
            if bare_lower in _SURNAME_PARTICLES:
                collected.append(token)
                continue
            if bare_lower in conjunctions_lower:
                collected.append(token)
                state = EXPECT_SURNAME
                continue
            if bare_lower in et_al_parts:
                collected.append(token)
                continue

            # Compound-surname extension: a second capitalised token
            # immediately adjacent to the surname just collected
            # belongs to the same author (Sancı Uzun, Çakır İlhan,
            # Ercan Güven, Öztürk Pat). Without this, "Öztürk Pat
            # (2017)" collapses to "Pat (2017)" and never matches the
            # reference key "ozturk pat:2017". Guarded by:
            #   * the candidate is fully capitalised and has no
            #     trailing sentence punctuation of its own;
            #   * the candidate is not a function word that happens
            #     to start a sentence ("As", "See", "In", "Gibi", …);
            #   * the token one step further back in the walk does
            #     not end with ".", "!", "?", ":", so
            #     "... Aykaç. Öztürk Pat (2020)" stops at "Pat"
            #     rather than swallowing "Aykaç".
            if (
                compound_extensions < _MAX_COMPOUND_EXTENSIONS
                and bare[0].isalpha()
                and bare[0].isupper()
                and token[-1] not in ".!?:"
                and bare_lower not in _COMPOUND_SURNAME_BLOCKERS
            ):
                next_token = window[idx - 1] if idx > 0 else ""
                if not next_token or next_token[-1] not in ".!?:":
                    collected.append(token)
                    compound_extensions += 1
                    continue

            break

        if not collected:
            return ""

        collected.reverse()
        return " ".join(collected)

    def _find_narrative_authors(
        self, text: str, paren_start: int,
    ) -> tuple[list[str], str, bool]:
        """
        Look up to :data:`_NARRATIVE_LOOKBACK_WORDS` words before
        *paren_start* for a likely author phrase.

        Runs two walks:

        1. Profile-only walk (uses self.profile.conjunctions). Its
           result is split into *authors* and is identical to the
           pre-fix behavior. Matching is decided by this list alone,
           so widening the walk below cannot accidentally turn a
           flagged citation into a match.

        2. Extended walk (uses ALL_LOOKBACK_CONJUNCTIONS, the union
           across all profiles). Used for display only, and only when
           it produces a longer phrase than the profile-only walk -
           which happens iff the walk stepped over a conjunction that
           is not part of the active profile (a "foreign conjunction",
           e.g. "ve" under the English profile). That is precisely the
           class of cross-language citation errors this method exists
           to surface.

        Returns:
            ``(authors, display_phrase, has_foreign_conjunction)``.
            ``display_phrase`` is "" unless a foreign conjunction was
            present, in which case it is the fuller walked-back phrase
            including the foreign conjunction and its preceding
            surname. The caller prepends it to the citation's raw form
            when *has_foreign_conjunction* is True.
        """
        profile_phrase = self._walk_narrative_phrase(
            text, paren_start, self.profile.conjunctions,
        )
        profile_phrase = self._strip_leading_markers(profile_phrase)
        if not profile_phrase:
            return [], "", False

        extended_phrase = self._walk_narrative_phrase(
            text, paren_start, ALL_LOOKBACK_CONJUNCTIONS,
        )
        extended_phrase = self._strip_leading_markers(extended_phrase)

        authors = self._split_authors(profile_phrase)

        if not extended_phrase or extended_phrase == profile_phrase:
            return authors, "", False

        return authors, extended_phrase, True

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