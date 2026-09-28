"""Reusable verification runner shared by CLI and GUI."""

from pathlib import Path
from typing import Callable, Optional
from models import Reference
from verification.crossref_provider import CrossrefProvider
from verification.openlibrary_provider import OpenLibraryProvider
from verification.service import VerificationService
from report.generator import ReportGenerator
from report.exporter import ReportExporter


def run_verification(document_path: Path, output_dir: Path) -> dict:
    """Extract references from a DOCX, verify them, and return a report."""
    processor = ManuscriptProcessor()
    references = processor.extract_references(document_path)
    return _verify_and_report(references, output_dir, progress_callback=None, source_name=document_path.name)


def verify_references(
    references: list[Reference],
    output_dir: Path,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    source_name: Optional[str] = None,
) -> dict:
    """Verify a list of references, optionally reporting progress and labelling source."""
    return _verify_and_report(references, output_dir, progress_callback, source_name)


def _verify_and_report(
    references: list[Reference],
    output_dir: Path,
    progress_callback: Optional[Callable[[int, int], None]],
    source_name: Optional[str],
) -> dict:
    """Internal helper: verify references and generate report."""
    service = VerificationService(
        providers=[
            CrossrefProvider(),
            OpenLibraryProvider(),
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