"""
Serialization helpers for verification results.

Round-trips VerificationResult, including nested VerificationEvidence
and ReferenceMatch objects, to JSON-safe dicts and back. The full
payload is preserved so a cached result behaves identically to a live
one — specifically, the evidence.matches that ReportGenerator reads
for titles.
"""

from datetime import datetime

from models import (
    Provider,
    ReferenceMatch,
    ReferenceType,
    VerificationEvidence,
    VerificationResult,
    VerificationStatus,
)


def result_to_dict(result: VerificationResult) -> dict:
    """
    Convert VerificationResult to JSON-safe data.
    """
    return {
        "status": result.status.value,
        "confidence": result.confidence,
        "explanation": result.explanation,
        "warnings": list(result.warnings),
        "search_url": result.search_url,
        "url": result.url,
        "url_status": result.url_status,
        "evidence": _evidence_to_dict(result.evidence),
    }


def dict_to_result(data: dict) -> VerificationResult:
    """
    Reconstruct a VerificationResult from a dict produced by
    :func:`result_to_dict`. Missing keys degrade to empty defaults so
    older cache entries never raise.
    """
    return VerificationResult(
        status=VerificationStatus(data["status"]),
        confidence=data.get("confidence", 0.0),
        explanation=data.get("explanation", ""),
        warnings=list(data.get("warnings", [])),
        search_url=data.get("search_url"),
        url=data.get("url"),
        url_status=data.get("url_status"),
        evidence=_dict_to_evidence(data.get("evidence")),
    )


def _evidence_to_dict(evidence: VerificationEvidence | None) -> dict | None:
    if evidence is None:
        return None
    return {
        "matches": [_match_to_dict(m) for m in evidence.matches],
        "providers_checked": [
            p.value if hasattr(p, "value") else str(p)
            for p in evidence.providers_checked
        ],
        "doi_found": evidence.doi_found,
        "cache_hit": evidence.cache_hit,
        "verification_time": (
            evidence.verification_time.isoformat()
            if evidence.verification_time
            else None
        ),
        "notes": list(evidence.notes),
    }

def _str_to_provider(value: str) -> Provider | str:
    """
    Restore a provider identifier. If it matches a Provider member,
    return the enum; otherwise keep the raw string. Some tests and
    custom providers use names that are not in the enum.
    """
    try:
        return Provider(value)
    except ValueError:
        return value

def _dict_to_evidence(data: dict | None) -> VerificationEvidence:
    if data is None:
        return VerificationEvidence()
    return VerificationEvidence(
        matches=[_dict_to_match(m) for m in data.get("matches", [])],
        providers_checked=[
            _str_to_provider(p) for p in data.get("providers_checked", [])
        ],
        doi_found=data.get("doi_found"),
        cache_hit=data.get("cache_hit", False),
        verification_time=(
            datetime.fromisoformat(data["verification_time"])
            if data.get("verification_time")
            else None
        ),
        notes=list(data.get("notes", [])),
    )


def _match_to_dict(match: ReferenceMatch) -> dict:
    return {
        "provider": match.provider.value,
        "reference_type": match.reference_type.value,
        "record_id": match.record_id,
        "title": match.title,
        "authors": list(match.authors) if match.authors else None,
        "journal": match.journal,
        "book_title": match.book_title,
        "editors": list(match.editors) if match.editors else None,
        "publisher": match.publisher,
        "publisher_location": match.publisher_location,
        "isbn": match.isbn,
        "edition": match.edition,
        "year": match.year,
        "doi": match.doi,
        "url": match.url,
        "title_similarity": match.title_similarity,
        "author_similarity": match.author_similarity,
        "book_title_similarity": match.book_title_similarity,
        "editor_similarity": match.editor_similarity,
        "publisher_similarity": match.publisher_similarity,
        "year_match": match.year_match,
        "doi_match": match.doi_match,
        "overall_score": match.overall_score,
        "evidence_weight": match.evidence_weight,
    }


def _dict_to_match(data: dict) -> ReferenceMatch:
    return ReferenceMatch(
        provider=Provider(data["provider"]),
        reference_type=ReferenceType(
            data.get("reference_type", "unknown")
        ),
        record_id=data.get("record_id"),
        title=data.get("title"),
        authors=list(data["authors"]) if data.get("authors") else None,
        journal=data.get("journal"),
        book_title=data.get("book_title"),
        editors=list(data["editors"]) if data.get("editors") else None,
        publisher=data.get("publisher"),
        publisher_location=data.get("publisher_location"),
        isbn=data.get("isbn"),
        edition=data.get("edition"),
        year=data.get("year"),
        doi=data.get("doi"),
        url=data.get("url"),
        title_similarity=data.get("title_similarity"),
        author_similarity=data.get("author_similarity"),
        book_title_similarity=data.get("book_title_similarity"),
        editor_similarity=data.get("editor_similarity"),
        publisher_similarity=data.get("publisher_similarity"),
        year_match=data.get("year_match"),
        doi_match=data.get("doi_match"),
        overall_score=data.get("overall_score"),
        evidence_weight=data.get("evidence_weight"),
    )