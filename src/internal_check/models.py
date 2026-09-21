"""
Internal-check data models.

Represents in-text citations, internal-consistency issues, and the
overall result of an internal check.
"""

from dataclasses import dataclass, field
from enum import Enum

from models import Reference


class CitationKind(str, Enum):
    """How an in-text citation is expressed."""

    PARENTHETICAL = "parenthetical"
    NARRATIVE = "narrative"
    NUMERIC = "numeric"
    UNKNOWN = "unknown"


class IssueType(str, Enum):
    """Kind of problem found by the internal check."""

    MISSING_REFERENCE = "missing_reference"
    UNCITED_REFERENCE = "uncited_reference"
    AMBIGUOUS = "ambiguous"
    UNPARSED = "unparsed"


@dataclass
class InTextCitation:
    """One in-text citation extracted from manuscript body text."""

    raw: str

    kind: CitationKind = CitationKind.UNKNOWN

    authors: list[str] = field(default_factory=list)
    year: int | None = None
    year_suffix: str | None = None

    # For numeric citation styles, e.g. [1,3-5] -> [1, 3, 4, 5]
    numbers: list[int] = field(default_factory=list)

    # Free-form location label, e.g. "paragraph 12"
    location: str | None = None

    # 0.0 (low confidence) to 1.0 (certain)
    confidence: float = 1.0


@dataclass
class InternalCheckIssue:
    """A single internal-consistency problem found."""

    issue_type: IssueType
    message: str

    citation: InTextCitation | None = None
    reference: Reference | None = None

    confidence: float = 1.0


@dataclass
class InternalCheckResult:
    """Overall result of an internal check."""

    citations: list[InTextCitation] = field(default_factory=list)
    issues: list[InternalCheckIssue] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def missing_references(self) -> list[InternalCheckIssue]:
        """Return only the issues of type MISSING_REFERENCE."""
        return [
            issue
            for issue in self.issues
            if issue.issue_type == IssueType.MISSING_REFERENCE
        ]

    def uncited_references(self) -> list[InternalCheckIssue]:
        """Return only the issues of type UNCITED_REFERENCE."""
        return [
            issue
            for issue in self.issues
            if issue.issue_type == IssueType.UNCITED_REFERENCE
        ]