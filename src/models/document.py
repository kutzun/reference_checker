"""
Document data model.

Represents a manuscript being processed by Reference Checker.
"""

from dataclasses import dataclass, field
from pathlib import Path

from .enums import ProcessingStatus
from .reference import Reference
from .verification_result import VerificationResult


@dataclass
class Document:
    """
    Represents one document submitted for verification.

    The document stores processing information and references extracted
    from the bibliography.
    """

    file_path: Path

    references: list[Reference] = field(default_factory=list)

    results: list[VerificationResult] = field(default_factory=list)

    status: ProcessingStatus = ProcessingStatus.NOT_STARTED

    error_message: str | None = None

    def add_reference(self, reference: Reference) -> None:
        """
        Add an extracted reference.

        Args:
            reference:
                Parsed bibliographic reference.
        """
        self.references.append(reference)

    def add_result(self, result: VerificationResult) -> None:
        """
        Add a verification result.

        Args:
            result:
                Completed verification result.
        """
        self.results.append(result)

    @property
    def filename(self) -> str:
        """
        Return the document filename.

        Returns:
            Name of the file without directory path.
        """
        return self.file_path.name

    @property
    def reference_count(self) -> int:
        """
        Return the number of extracted references.

        Returns:
            Number of references.
        """
        return len(self.references)

    @property
    def verified_count(self) -> int:
        """
        Return the number of completed verification results.

        Returns:
            Number of verification results.
        """
        return len(self.results)
