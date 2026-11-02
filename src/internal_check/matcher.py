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

from models import Reference

from .models import (
    CitationKind,
    InTextCitation,
    InternalCheckIssue,
    InternalCheckResult,
    IssueType,
)
from .normalizer import citation_key


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
        # Build reference key map
        # ------------------------------------------------------------------
        ref_by_key: dict[str, list[Reference]] = {}
        for ref in references:
            key = _reference_key(ref)
            if not key:
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
            ref_by_key.setdefault(key, []).append(ref)

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

        cited_keys: set[str] = set()
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

            matches = ref_by_key.get(key, [])
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
                cited_keys.add(key)
            else:
                cited_keys.add(key)

        # ------------------------------------------------------------------
        # Author-year pass: check each reference for being cited
        # ------------------------------------------------------------------
        if has_author_year:
            for key, refs in ref_by_key.items():
                if key in cited_keys:
                    continue
                for ref in refs:
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