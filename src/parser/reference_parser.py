"""
Builds Reference objects from bibliography entries.
"""

from extractor.metadata import (
    extract_metadata,
)
from models import (
    Reference,
)


class ReferenceParser:
    """
    Converts raw reference strings into Reference objects.
    """

    def parse(
        self,
        entries: list[str],
    ) -> list[Reference]:
        """
        Parse reference entries.

        Args:
            entries:
                Raw bibliography entries.

        Returns:
            Parsed references.
        """

        references: list[Reference] = []

        for entry in entries:

            reference = Reference(
                raw_text=entry,
            )

            reference = extract_metadata(
                reference,
            )

            references.append(
                reference,
            )

        return references