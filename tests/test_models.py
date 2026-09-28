"""
Tests for Reference Checker core data models.
"""

from pathlib import Path

from models import (
    Document,
    ProcessingStatus,
    Provider,
    Reference,
    ReferenceMatch,
    ReferenceType,
    VerificationEvidence,
    VerificationResult,
    VerificationStatus,
)


def test_reference_creation():
    reference = Reference(
        raw_text="Smith, J. (2025). Example article.",
        title="Example article",
        reference_type=ReferenceType.JOURNAL_ARTICLE,
    )

    assert reference.title == "Example article"
    assert reference.has_minimum_metadata()
    assert not reference.has_doi()


def test_reference_match():
    match = ReferenceMatch(
        provider=Provider.CROSSREF,
        title="Example article",
        overall_score=0.95,
    )

    assert match.is_strong_match()


def test_verification_evidence():
    evidence = VerificationEvidence()

    match = ReferenceMatch(
        provider=Provider.CROSSREF,        # Changed from OPENALEX
        overall_score=0.85,
    )

    evidence.add_match(match)
    evidence.add_provider(Provider.CROSSREF)  # Changed from OPENALEX

    assert len(evidence.matches) == 1
    assert evidence.best_match() == match
    assert Provider.CROSSREF in evidence.providers_checked   # Updated assertion


def test_verification_result():
    result = VerificationResult(
        status=VerificationStatus.VERIFIED,
        confidence=0.95,
    )

    assert result.is_verified()
    assert not result.requires_review()


def test_document():
    document = Document(
        file_path=Path("example.docx"),
        status=ProcessingStatus.NOT_STARTED,
    )

    reference = Reference(
        raw_text="Example reference",
    )

    document.add_reference(reference)

    assert document.filename == "example.docx"
    assert document.reference_count == 1