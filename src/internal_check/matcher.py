"""
Internal consistency matcher.

Compares extracted in-text citations against the reference list and
produces issues: missing references, uncited references, ambiguous
matches, and items that could not be checked.

Language-independent by design: it never inspects words, only the
normalized keys produced by ``normalizer.py``. English and Turkish
flow through the same code path.

Numeric citations are matched by position in the reference list:
``[1]`` refers to the first reference, ``[2]`` to the second, etc.
"""

import re

from models import Reference

from .models import (
    CitationKind,
    InTextCitation,
    InternalCheckIssue,
    InternalCheckResult,
    IssueType,
)
from .normalizer import citation_key


# Trailing parenthetical acronym in an institutional author name:
#   "Millî Eğitim Bakanlığı (MEB)"  -> "MEB"
#   "World Health Organization (WHO)" -> "WHO"
# Requires 2+ consecutive uppercase letters so "(A)", "(Ed.)", and
# title-internal parentheticals do not spuriously qualify.
_ACRONYM_TAIL_RE = re.compile(r"\(\s*([A-ZÇĞİÖŞÜ]{2,})\s*\)\s*$")


def _acronym_alias(author: str) -> str | None:
    """Return a trailing parenthetical acronym from an author name, if
    one exists. Only trailing parentheses count — "(MEB) Committee"
    and "Foo (MEB) Bar" are not aliased."""
    m = _ACRONYM_TAIL_RE.search(author)
    return m.group(1) if m else None


def _reference_keys(reference: Reference) -> list[str]:
    """Return every matching key derivable from a reference.

    The first entry is always the primary key (first-author surname
    + year). If the first author ends in a parenthetical acronym,
    a second alias key is added so a citation that uses the acronym
    ("MEB, 2024") resolves against a reference whose author field
    holds the full institutional name
    ("Millî Eğitim Bakanlığı (MEB)"). Both keys point at the same
    Reference object — aliasing cannot inflate issue counts.

    Returns an empty list if the reference has no first author or no
    year; callers emit UNPARSED for such rows.
    """
    if not reference.authors or reference.year is None:
        return []

    primary = citation_key(
        reference.authors[0],
        reference.year,
        reference.year_suffix,
    )
    if not primary:
        return []

    keys = [primary]
    alias = _acronym_alias(reference.authors[0])
    if alias:
        alias_key = citation_key(
            alias, reference.year, reference.year_suffix
        )
        if alias_key and alias_key != primary:
            keys.append(alias_key)
    return keys


def _reference_key(reference: Reference) -> str:
    """Primary key only. Kept as a thin wrapper for callers that want
    just the first-author key; new code should prefer
    ``_reference_keys``."""
    keys = _reference_keys(reference)
    return keys[0] if keys else ""


def _intext_key(citation: InTextCitation) -> str:
    """Derive a matching key from an author-year in-text citation."""
    if not citation.authors or citation.year is None:
        return ""
    return citation_key(
        citation.authors[0],
        citation.year,
        citation.year_suffix,
    )


def _reference_key(reference: Reference) -> str:
    """Derive a matching key from a reference-list entry."""
    if not reference.authors or reference.year is None:
        return ""
    return citation_key(
        reference.authors[0],
        reference.year,
        reference.year_suffix,
    )


class InternalMatcher:
    """
    Compares citations against references and reports inconsistencies.
    """

    def match(
        self,
        citations: list[InTextCitation],
        references: list[Reference],
    ) -> InternalCheckResult:
        """
        Run the internal consistency check.

        Args:
            citations: In-text citations found in the body text.
            references: Parsed reference-list entries.

        Returns:
            An :class:`InternalCheckResult` containing all issues.
        """
        result = InternalCheckResult()
        result.citations = list(citations)

        # ------------------------------------------------------------------
        # Build reference key index
        #
        # Each reference may contribute more than one key: the primary
        # first-author key plus an optional trailing-acronym alias.
        # Both keys point at the same Reference object, so an alias
        # match does not create a duplicate Uncited issue and a
        # non-match does not double-flag.
        # ------------------------------------------------------------------
        entries: list[tuple[Reference, list[str]]] = []
        key_index: dict[str, list[Reference]] = {}
        for ref in references:
            keys = _reference_keys(ref)
            if not keys:
                result.issues.append(
                    InternalCheckIssue(
                        issue_type=IssueType.UNPARSED,
                        message=(
                            "Reference lacks enough metadata for matching "
                            f"(no author or no year): {ref.raw_text[:80]!r}"
                        ),
                        reference=ref,
                        confidence=0.5,
                    )
                )
                continue
            entries.append((ref, keys))
            for k in keys:
                key_index.setdefault(k, []).append(ref)

        # ------------------------------------------------------------------
        # Decide which checks apply
        # ------------------------------------------------------------------
        has_author_year = any(
            c.kind != CitationKind.NUMERIC for c in citations
        )
        has_numeric = any(
            c.kind == CitationKind.NUMERIC for c in citations
        )
        
        if not citations:
            has_author_year = True

        cited_ref_ids: set[int] = set()
        cited_numbers: set[int] = set()

        # ------------------------------------------------------------------
        # Author-year pass: check each citation
        # ------------------------------------------------------------------
        for c in citations:
            if c.kind == CitationKind.NUMERIC:
                cited_numbers.update(c.numbers)
                continue

            key = _intext_key(c)
            if not key:
                result.issues.append(
                    InternalCheckIssue(
                        issue_type=IssueType.UNPARSED,
                        message=f"Could not derive a key from citation: {c.raw!r}",
                        citation=c,
                        confidence=0.5,
                    )
                )
                continue

            matches = key_index.get(key, [])
            if not matches:
                result.issues.append(
                    InternalCheckIssue(
                        issue_type=IssueType.MISSING_REFERENCE,
                        message=(
                            "In-text citation has no matching reference: "
                            f"{c.raw!r}"
                        ),
                        citation=c,
                        confidence=c.confidence,
                    )
                )
            elif len(matches) > 1:
                result.issues.append(
                    InternalCheckIssue(
                        issue_type=IssueType.AMBIGUOUS,
                        message=(
                            f"Citation {c.raw!r} matches "
                            f"{len(matches)} references"
                        ),
                        citation=c,
                        confidence=c.confidence,
                    )
                )
                for r in matches:
                    cited_ref_ids.add(id(r))
            else:
                cited_ref_ids.add(id(matches[0]))

        # ------------------------------------------------------------------
        # Author-year pass: check each reference for being cited
        #
        # Iterate `entries` (one row per reference), not `key_index`,
        # so a reference with multiple keys is checked once. A
        # reference counts as cited iff AT LEAST ONE of its keys was
        # hit by any citation.
        # ------------------------------------------------------------------
        if has_author_year:
            for ref, _keys in entries:
                if id(ref) in cited_ref_ids:
                    continue
                result.issues.append(
                    InternalCheckIssue(
                        issue_type=IssueType.UNCITED_REFERENCE,
                        message=(
                            "Reference is not cited in text: "
                            f"{ref.raw_text[:80]!r}"
                        ),
                        reference=ref,
                        confidence=0.9,
                    )
                )

        # ------------------------------------------------------------------
        # Numeric pass
        # ------------------------------------------------------------------
        if has_numeric:
            for n in sorted(cited_numbers):
                if n < 1 or n > len(references):
                    result.issues.append(
                        InternalCheckIssue(
                            issue_type=IssueType.MISSING_REFERENCE,
                            message=(
                                f"Numeric citation [{n}] has no "
                                f"corresponding reference "
                                f"(list has {len(references)} entries)"
                            ),
                            confidence=0.95,
                        )
                    )
            for i in range(1, len(references) + 1):
                if i not in cited_numbers:
                    result.issues.append(
                        InternalCheckIssue(
                            issue_type=IssueType.UNCITED_REFERENCE,
                            message=(
                                f"Reference #{i} is not cited in text: "
                                f"{references[i - 1].raw_text[:80]!r}"
                            ),
                            reference=references[i - 1],
                            confidence=0.95,
                        )
                    )

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        result.summary = {
            "citations_found": len(citations),
            "references_found": len(references),
            "missing_references": len(result.missing_references()),
            "uncited_references": len(result.uncited_references()),
            "ambiguous": sum(
                1
                for i in result.issues
                if i.issue_type == IssueType.AMBIGUOUS
            ),
            "unparsed": sum(
                1
                for i in result.issues
                if i.issue_type == IssueType.UNPARSED
            ),
        }

        return result