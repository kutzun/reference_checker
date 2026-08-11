"""
Command-line interface for Reference Checker.
"""

import argparse
from pathlib import Path

from report.exporter import ReportExporter
from report.generator import ReportGenerator
from verification.crossref_provider import CrossrefProvider
from verification.openlibrary_provider import OpenLibraryProvider
from verification.service import VerificationService
from workflow.manuscript import ManuscriptProcessor
from workflow.verifier import ManuscriptVerifier


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Verify bibliography references in DOCX manuscripts."
    )
    parser.add_argument(
        "document",
        type=Path,
        help="Path to DOCX manuscript.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Output directory.",
    )
    return parser


def main() -> None:
    """Run reference verification."""
    parser = create_parser()
    args = parser.parse_args()

    # 1. Extract references from manuscript
    processor = ManuscriptProcessor()
    references = processor.extract_references(args.document)

    # 2. Set up free providers (Crossref + OpenLibrary)
    service = VerificationService(
        providers=[
            CrossrefProvider(),
            OpenLibraryProvider(),
        ],
    )

    # 3. Verify references
    verifier = ManuscriptVerifier(service)
    results = verifier.verify_references(references)

    # 4. Generate and export reports
    report = ReportGenerator().generate_detailed_report(results)  

    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    exporter = ReportExporter()
    exporter.export_json(report, output_dir / "report.json")
    exporter.export_csv(report, output_dir / "report.csv")

    print("Reference verification complete.")
    print(f"References checked: {report['summary']['total']}")

if __name__ == "__main__":
    main()