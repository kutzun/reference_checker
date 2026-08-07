"""
Builds Reference objects from bibliography entries.
"""

from extractor.patterns import (
    find_doi,
    find_url,
    find_year,
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

        references = []

        for entry in entries:

            references.append(
                Reference(
                    raw_text=entry,
                    year=find_year(entry),
                    doi=find_doi(entry),
                    url=find_url(entry),
                )
            )

        return references
