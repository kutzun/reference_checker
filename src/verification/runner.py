"""Reusable verification runner shared by CLI and GUI."""

from pathlib import Path
from typing import Callable, Optional

from config.settings import (
    get_crossref_email,
    get_google_books_api_key,
)
from models import Reference
from report.exporter import ReportExporter
from report.generator import ReportGenerator
from verification.crossref_provider import CrossrefProvider
from verification.doi_org_provider import DoiOrgProvider
from verification.google_books_provider import GoogleBooksProvider
from verification.openlibrary_provider import OpenLibraryProvider
from verification.service import VerificationService
from verification.tr_dizin_provider import TrDizinProvider
from workflow.manuscript import ManuscriptProcessor


def run_verification(document_path: Path, output_dir: Path) -> dict:
    """Extract references from a DOCX, verify them, and return a report."""
    processor = ManuscriptProcessor()
    references = processor.extract_references(document_path)
    return _verify_and_report(
        references,
        output_dir,
        progress_callback=None,
        source_name=document_path.name,
    )


def verify_references(
    references: list[Reference],
    output_dir: Path,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    source_name: Optional[str] = None,
) -> dict:
    """Verify a list of references, optionally reporting progress and labelling source."""
    return _verify_and_report(
        references, output_dir, progress_callback, source_name
    )


def _verify_and_report(
    references: list[Reference],
    output_dir: Path,
    progress_callback: Optional[Callable[[int, int], None]],
    source_name: Optional[str],
) -> dict:
    """Internal helper: verify references and generate report."""
    crossref_email = get_crossref_email()
    google_books_key = get_google_books_api_key()

    service = VerificationService(
        providers=[
            DoiOrgProvider(),
            CrossrefProvider(email=crossref_email),
            TrDizinProvider(),
            # OpenLibrary runs before Google Books to conserve the
            # user's Google API quota: keyless providers get first
            # shot at every reference, and Google Books only fires
            # when nothing else has verified.
            OpenLibraryProvider(),
            GoogleBooksProvider(api_key=google_books_key),
        ],
    )

    results = []
    total = len(references)
    for idx, ref in enumerate(references, 1):
        result = service.verify(ref)
        results.append(result)
        if progress_callback:
            progress_callback(idx, total)

    report = ReportGenerator().generate_detailed_report(results)

    # Attach raw_text and source to each reference entry
    for i, ref_dict in enumerate(report["references"]):
        if i < len(references):
            raw_text = references[i].raw_text
            if raw_text:
                ref_dict["raw_text"] = raw_text
        if source_name:
            ref_dict["source"] = source_name

    output_dir.mkdir(parents=True, exist_ok=True)
    exporter = ReportExporter()
    exporter.export_json(report, output_dir / "report.json")
    exporter.export_csv(report, output_dir / "report.csv")

    return report