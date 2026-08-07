"""
Command-line interface for Reference Checker.
"""

import argparse
from pathlib import Path

from report.exporter import (
    ReportExporter,
)
from report.generator import (
    ReportGenerator,
)
from verification.service import (
    VerificationService,
)
from workflow.manuscript import (
    ManuscriptProcessor,
)
from workflow.verifier import (
    ManuscriptVerifier,
)


def create_parser() -> argparse.ArgumentParser:
    """
    Create CLI argument parser.

    Returns:
        Configured argument parser.
    """

    parser = argparse.ArgumentParser(
        description=("Verify bibliography references " "in DOCX manuscripts.")
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
    """
    Run reference verification.
    """

    parser = create_parser()

    args = parser.parse_args()

    processor = ManuscriptProcessor()

    references = processor.extract_references(args.document)

    service = VerificationService(providers=[])

    verifier = ManuscriptVerifier(service)

    results = verifier.verify_references(references)

    report = ReportGenerator().generate_summary(results)

    exporter = ReportExporter()

    exporter.export_json(
        report,
        args.output / "report.json",
    )

    exporter.export_csv(
        report,
        args.output / "report.csv",
    )

    print("Reference verification complete.")

    print(f"References checked: {report['total']}")


if __name__ == "__main__":
    main()
