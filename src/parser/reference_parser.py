"""
Builds Reference objects from bibliography entries.
"""

import re

from extractor.metadata import (
    extract_metadata,
)
from models import (
    Reference,
)


# Repeated-author marker at the start of a bibliography entry.
# Covers the common variants: ——— (Chicago em-dashes), --- (3 hyphens),
# ------ (6 hyphens), ––– (3 en-dashes). Any run of 3+ dash characters
# at the start of the entry is treated as a repeated-author marker.
_REPEATED_AUTHOR_RE = re.compile(r"^\s*[—–-]{3,}\.?")


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

        Consecutive entries where a later one begins with a repeated-
        author marker (———, ---, ------, –––) inherit the previous
        entry's authors.

        Args:
            entries:
                Raw bibliography entries.

        Returns:
            Parsed references.
        """

        references: list[Reference] = []

        previous_authors: list[str] = []

        for entry in entries:

            reference = Reference(
                raw_text=entry,
            )

            reference = extract_metadata(
                reference,
            )

            if _REPEATED_AUTHOR_RE.match(entry):
                # Copy the previous entry's authors. If this is the
                # first entry of a bibliography, previous_authors is
                # empty and authors is cleared, which is correct.
                reference.authors = list(previous_authors)

            previous_authors = reference.authors

            references.append(
                reference,
            )

        return references