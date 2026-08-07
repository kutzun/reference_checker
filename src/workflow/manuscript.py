"""
Manuscript processing pipeline.

Extracts references from DOCX files.
"""

from pathlib import Path

from models import (
    Reference,
)
from parser.docx_parser import (
    DocxParser,
)
from parser.reference_parser import (
    ReferenceParser,
)


class ManuscriptProcessor:
    """
    Converts a DOCX manuscript into Reference objects.
    """

    def __init__(
        self,
        reference_parser: ReferenceParser | None = None,
    ):
        """
        Initialize processor.
        """

        self.reference_parser = (
            reference_parser if reference_parser is not None else ReferenceParser()
        )

    def extract_references(
        self,
        file_path: Path,
    ) -> list[Reference]:
        """
        Extract references from DOCX.

        Args:
            file_path:
                Manuscript path.

        Returns:
            Parsed references.
        """

        parser = DocxParser(file_path)

        entries = parser.extract_reference_section()

        return self.reference_parser.parse(entries)
